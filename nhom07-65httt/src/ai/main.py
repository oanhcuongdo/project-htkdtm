"""Learning Hub AI Service - Main FastAPI Application."""

import base64
import binascii
import os
import re
import secrets
from contextlib import asynccontextmanager

import json as _json
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.gzip import GZipMiddleware
from starlette.concurrency import run_in_threadpool

from src.core.clients import get_qdrant_client
from src.core.config import settings
from src.core.rate_limit import enforce_chat_rate_limit
from src.schemas.requests import (
    EssayGradeRequest,
    FlashcardGenerateRequest,
    MindmapGenerateRequest,
    QueryRequest,
    QuizGenerateFromLessonRequest,
    QuizGenerateRequest,
    RemedialQuizRequest,
)
from src.schemas.responses import (
    ChatResponse,
    Citation,
    EssayGradeResponse,
    FlashcardGenerateResponse,
    FlashcardItem,
    MindmapGenerateResponse,
    QuizGenerateResponse,
    QuizQuestion,
    TokenUsage,
)
from src.workflows.graph import build_graph

workflow = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize lightweight clients on startup.

    NOTE: the sentence-transformer embedding model (~500MB) is loaded LAZILY
    on first use, never at startup — preloading it OOM-kills small dynos and
    makes /health probes fail before the service can serve traffic.
    Each init step is isolated so one failing dependency (e.g. missing API
    key) never prevents the whole service from booting.
    """
    global workflow
    import logging
    log = logging.getLogger("ai.lifespan")
    try:
        get_qdrant_client()
    except Exception as exc:
        log.warning("Qdrant init deferred: %s", exc)
    try:
        workflow = build_graph()
    except Exception as exc:
        log.warning("Workflow build deferred: %s", exc)
        workflow = None

    # Warm up SentenceTransformer model in a background daemon thread
    # so first user request doesn't suffer 20-40s cold-start latency,
    # while keeping /health and /ready probes fast and unblocked.
    import threading

    def _warmup_embeddings():
        import time
        time.sleep(3)
        try:
            from src.utils.embeddings import get_embedding_model
            get_embedding_model()
            log.info("SentenceTransformer embedding model warmed up successfully")
        except Exception as exc:
            log.warning("Embedding model warmup deferred: %s", exc)

    threading.Thread(target=_warmup_embeddings, daemon=True).start()

    yield


app = FastAPI(
    title="Learning Hub AI Service",
    description="AI/LLM Services for Multimodal Learning Hub",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


async def verify_internal_key(x_internal_api_key: str = Header(..., alias="X-Internal-API-Key")):
    """Verify the shared internal API key for service-to-service communication."""
    if not secrets.compare_digest(x_internal_api_key, settings.INTERNAL_API_KEY):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Internal API Key")
    return x_internal_api_key


@app.get("/")
def root():
    return {"message": "Learning Hub AI Service", "status": "running"}


@app.get("/health")
def health_check():
    """Verify health of connection pools and AI models.

    NOTE: embedding model load is lazy — the /health probe must NOT force a
    ~500MB model download into RAM during a health probe.
    """
    status_info = {
        "status": "healthy",
        "qdrant": "unknown",
        "embedding_model": "lazy",
    }

    # Ping Qdrant
    try:
        client = get_qdrant_client()
        client.get_collections()
        status_info["qdrant"] = "healthy"
    except Exception:
        status_info["qdrant"] = "unhealthy"
        status_info["status"] = "degraded"

    return status_info


@app.get("/ready")
def readiness_check():
    return {"ready": True}


@app.post("/chat/ask", response_model=ChatResponse)
async def chat_ask(
    payload: QueryRequest,
    _=Depends(verify_internal_key),
    __=Depends(enforce_chat_rate_limit),
) -> ChatResponse:
    """Process a chat query through the asynchronous AI workflow.

    Supports both personal documents (document_ids), course-scoped RAG (course_id),
    and lesson-scoped RAG (lesson_id).
    When lesson_id is provided, retrieves only from that lesson.
    When course_id is provided (without lesson_id), retrieves from all course content.
    """
    result = await workflow(
        query=payload.query,
        session_id=payload.session_id,
        user_id=payload.user_id,
        document_ids=payload.document_ids,
        course_id=payload.course_id,
        lesson_id=payload.lesson_id,
        course_title=payload.course_title,
        strict_course=payload.strict_course,
        chat_history=payload.chat_history or [],
        tutor_mode=getattr(payload, "tutor_mode", "standard") or "standard",
    )

    citations = [
        Citation(
            document_id=c.get("document_id", ""),
            chunk_id=c.get("chunk_id", ""),
            page_number=c.get("page_number"),
            text=c.get("text", ""),
            material_id=c.get("material_id", ""),
            course_id=c.get("course_id", ""),
            lesson_id=c.get("lesson_id", ""),
        )
        for c in result.get("citations", [])
    ]

    return ChatResponse(
        answer=result.get("answer", ""),
        citations=citations,
        token_usage=TokenUsage(),
    )


@app.post("/chat/ask/stream")
async def chat_ask_stream(
    payload: QueryRequest,
    _=Depends(verify_internal_key),
    __=Depends(enforce_chat_rate_limit),
):
    """Stream chat response via SSE. RAG pipeline runs sync, then Generator streams tokens."""
    import asyncio
    from src.agents.generator import generate_answer_stream
    from src.agents.grader import grade_chunks
    from src.agents.intent import classify_intent
    from src.agents.retriever import retrieve

    async def event_stream():
        try:
            # Step 1: Intent
            try:
                intent_result = await asyncio.wait_for(
                    asyncio.to_thread(classify_intent, payload.query), timeout=10.0
                )
                intent = intent_result.get("intent", "qa")
            except Exception:
                intent = "qa"

            # Greetings skip RAG entirely: answer directly with no citations.
            if intent == "greeting":
                from src.agents.generator import generate_greeting_reply
                full_greeting = generate_greeting_reply(
                    payload.query,
                    tutor_mode=getattr(payload, "tutor_mode", "standard") or "standard",
                    course_title=payload.course_title,
                    course_id=payload.course_id,
                )
                yield f"data: {_json.dumps({'type': 'meta', 'intent': intent, 'citations': []})}\n\n"
                yield f"data: {_json.dumps({'type': 'token', 'text': full_greeting})}\n\n"
                yield f"data: {_json.dumps({'type': 'done', 'answer': full_greeting})}\n\n"
                return

            # Step 2: Retrieve (Timeout 60s — matches non-stream workflow;
            # cold embedding model load ~500MB can take 20-50s on first use)
            try:
                if payload.course_id:
                    chunks = []
                    if payload.lesson_id:
                        chunks = await asyncio.wait_for(
                            asyncio.to_thread(
                                retrieve, payload.query,
                                course_id=payload.course_id, lesson_id=payload.lesson_id, limit=10,
                            ), timeout=60.0,
                        )
                    if not chunks:
                        chunks = await asyncio.wait_for(
                            asyncio.to_thread(
                                retrieve, payload.query,
                                course_id=payload.course_id, limit=10,
                            ), timeout=60.0,
                        )
                else:
                    chunks = await asyncio.wait_for(
                        asyncio.to_thread(
                            retrieve, payload.query,
                            document_ids=payload.document_ids or None,
                            user_id=payload.user_id or None, limit=10,
                        ), timeout=60.0,
                    )
                    # Soft user_id filter: retry without user_id when the
                    # strict filter yields nothing (mirrors retriever_node).
                    if not chunks and payload.document_ids and payload.user_id:
                        chunks = await asyncio.wait_for(
                            asyncio.to_thread(
                                retrieve, payload.query,
                                document_ids=payload.document_ids or None,
                                user_id=None, limit=10,
                            ), timeout=60.0,
                        )
            except Exception:
                chunks = []

            # Step 3: Grade (citation metadata enrichment happens inside
            # grade_chunks() via enrich_relevant_chunks(), shared with workflow).
            # If the grader times out or returns 0 relevant chunks:
            # - For course mode: only fall back if candidate chunks score >= 0.40,
            #   preserving course-priority redirect when off-topic
            # - For personal documents: fall back to top 5 chunks
            try:
                graded = await asyncio.wait_for(
                    asyncio.to_thread(grade_chunks, payload.query, chunks), timeout=15.0
                )
                relevant_chunks = graded.get("relevant_chunks", [])
            except Exception:
                relevant_chunks = []

            if not relevant_chunks and chunks:
                from src.agents.grader import enrich_relevant_chunks
                if payload.course_id:
                    candidates = [c for c in chunks if c.get("score", 0) >= 0.4][:5]
                    if candidates:
                        raw = [
                            {
                                "id": c.get("id", ""),
                                "text": (c.get("payload", {}) or {}).get("text", ""),
                                "score": c.get("score", 0),
                            }
                            for c in candidates
                        ]
                        relevant_chunks = enrich_relevant_chunks(raw, chunks)
                elif payload.document_ids:
                    raw = [
                        {
                            "id": c.get("id", ""),
                            "text": (c.get("payload", {}) or {}).get("text", ""),
                            "score": c.get("score", 0),
                        }
                        for c in chunks[:5]
                    ]
                    relevant_chunks = enrich_relevant_chunks(raw, chunks)

            citations = [
                {
                    "document_id": c.get("document_id", ""),
                    "chunk_id": c.get("id", ""),
                    "page_number": c.get("page_number"),
                    "text": c.get("text", "")[:200],
                    "course_id": c.get("course_id"),
                    "lesson_id": c.get("lesson_id"),
                    "material_id": c.get("material_id"),
                }
                for c in relevant_chunks
            ]
            yield f"data: {_json.dumps({'type': 'meta', 'intent': intent, 'citations': citations})}\n\n"

            # Step 4: Stream Generator
            chat_history = getattr(payload, "chat_history", None) or []
            tutor_mode = getattr(payload, "tutor_mode", "standard") or "standard"
            full_answer = ""
            try:
                async for token in generate_answer_stream(
                    payload.query,
                    relevant_chunks,
                    intent=intent,
                    chat_history=chat_history,
                    tutor_mode=tutor_mode,
                    course_id=payload.course_id,
                    course_title=payload.course_title,
                    strict_course=payload.strict_course,
                ):
                    full_answer += token
                    yield f"data: {_json.dumps({'type': 'token', 'text': token})}\n\n"
            except Exception as e:
                yield f"data: {_json.dumps({'type': 'error', 'message': str(e)})}\n\n"

            yield f"data: {_json.dumps({'type': 'done', 'answer': full_answer})}\n\n"

        except Exception as e:
            yield f"data: {_json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/study/quiz/generate", response_model=QuizGenerateResponse)
async def generate_quiz(payload: QuizGenerateRequest, _=Depends(verify_internal_key)) -> QuizGenerateResponse:
    """Generate quiz questions from context."""
    from src.agents.quiz import generate_quiz as _generate_quiz

    questions = _generate_quiz(payload.context, payload.quiz_type, payload.question_count)
    return QuizGenerateResponse(
        questions=[
            QuizQuestion(
                id=q["id"],
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation"),
            )
            for q in questions
        ]
    )


@app.post("/study/quiz/generate-from-lesson", response_model=QuizGenerateResponse)
async def generate_quiz_from_lesson(payload: QuizGenerateFromLessonRequest, _=Depends(verify_internal_key)) -> QuizGenerateResponse:
    """Retrieve lesson material context from Qdrant and generate quiz."""
    from src.agents.quiz import generate_quiz as _generate_quiz
    from src.agents.retriever import retrieve

    # 1. Retrieve chunks from Qdrant associated with the lesson
    chunks = retrieve(query="", lesson_id=payload.lesson_id, limit=20)
    
    # 2. Combine chunk texts
    retrieved_text = "\n".join([chunk["payload"].get("text", "") for chunk in chunks if chunk.get("payload")])
    
    # 3. Combine with direct lesson content if any
    context_parts = []
    if retrieved_text:
        context_parts.append(retrieved_text)
    if payload.lesson_content:
        context_parts.append(payload.lesson_content)
        
    context = "\n\n".join(context_parts)
    if not context:
        # Fallback empty context warning
        context = "No content available. Ask sample general questions."

    # 4. Generate quiz questions using the AI agent
    questions = _generate_quiz(context, "quick", payload.question_count)
    return QuizGenerateResponse(
        questions=[
            QuizQuestion(
                id=q["id"],
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation"),
            )
            for q in questions
        ]
    )


@app.post("/study/quiz/remedial", response_model=QuizGenerateResponse)
async def generate_remedial_quiz_endpoint(
    payload: RemedialQuizRequest, _=Depends(verify_internal_key)
) -> QuizGenerateResponse:
    """Generate targeted micro-quiz questions based on student's missed questions."""
    from src.agents.remedial_quiz import generate_remedial_quiz as _generate_remedial_quiz
    from src.agents.retriever import retrieve

    context = payload.lesson_content or ""
    if not context and payload.lesson_id:
        try:
            chunks = retrieve(query="", lesson_id=payload.lesson_id, limit=10)
            context = "\n".join([c["payload"].get("text", "") for c in chunks if c.get("payload")])
        except Exception:
            context = ""

    questions = _generate_remedial_quiz(
        missed_questions=payload.missed_questions,
        lesson_content=context,
        lesson_title=payload.lesson_title or "",
        question_count=payload.question_count,
    )
    return QuizGenerateResponse(
        questions=[
            QuizQuestion(
                id=q["id"],
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation"),
            )
            for q in questions
        ]
    )


@app.post("/study/flashcards/generate", response_model=FlashcardGenerateResponse)
async def generate_flashcards(payload: FlashcardGenerateRequest, _=Depends(verify_internal_key)) -> FlashcardGenerateResponse:
    """Generate flashcards from context."""
    from src.agents.flashcard import generate_flashcards as _generate_flashcards

    items = _generate_flashcards(payload.context, payload.set_name, payload.count)
    return FlashcardGenerateResponse(
        items=[
            FlashcardItem(id=item["id"], front=item["front"], back=item["back"])
            for item in items
        ]
    )


@app.post("/study/essay/grade", response_model=EssayGradeResponse)
async def grade_essay(payload: EssayGradeRequest, _=Depends(verify_internal_key)) -> EssayGradeResponse:
    """Grade essay by comparing with source context."""
    from src.agents.essay import grade_essay as _grade_essay
    from src.agents.retriever import retrieve

    context = payload.context or ""
    # Retrieve context from Qdrant if only document_id was provided
    if not context and getattr(payload, "document_id", None):
        results = retrieve(query=payload.essay_text, document_ids=[payload.document_id], user_id=payload.user_id, limit=5)
        context = "\n".join([r["payload"]["text"] for r in results]) if results else ""

    result = _grade_essay(context, payload.essay_text)
    return EssayGradeResponse(
        score=result.get("score", 0),
        feedback=result.get("feedback", ""),
        comparisons=result.get("comparisons", []),
    )


@app.post("/study/mindmap/generate", response_model=MindmapGenerateResponse)
async def generate_mindmap_endpoint(
    payload: MindmapGenerateRequest, _=Depends(verify_internal_key)
) -> MindmapGenerateResponse:
    """Generate Markdown hierarchy for interactive Mindmap rendering."""
    from src.agents.mindmap import generate_mindmap as _generate_mindmap

    tree = _generate_mindmap(payload.content, payload.title)
    return MindmapGenerateResponse(markdown_tree=tree)


@app.post("/internal/config/sync")
async def sync_ai_config(payload: dict, _=Depends(verify_internal_key)):
    """Replace runtime Gemini keys and model with the Admin database values."""
    from src.llm.key_rotator import GeminiKeyRotator
    from src.llm.runtime_config import set_gemini_model

    keys_list = payload.get("keys", [])
    if not isinstance(keys_list, list) or len(keys_list) > 100:
        raise HTTPException(status_code=400, detail="Invalid key list")
    model_id = payload.get("model_id")
    if not isinstance(model_id, str) or not re.fullmatch(r"gemini-[A-Za-z0-9._-]{1,93}", model_id):
        raise HTTPException(status_code=400, detail="Invalid Gemini model id")
    keys_list = [
        item for item in keys_list
        if isinstance(item, dict)
        and isinstance(item.get("api_key"), str)
        and 16 <= len(item["api_key"].strip()) <= 512
    ]
    GeminiKeyRotator.get_instance().sync_keys(keys_list)
    set_gemini_model(model_id)
    return {"synced": True, "count": len(keys_list), "model_id": model_id}


@app.get("/internal/keys/status")
async def get_keys_status(_=Depends(verify_internal_key)):
    """Get active key rotator status and masked key list."""
    from src.llm.key_rotator import GeminiKeyRotator

    return GeminiKeyRotator.get_instance().get_status()


@app.post("/internal/transcribe")
async def transcribe_audio_chunk(payload: dict, _=Depends(verify_internal_key)):
    """Transcribe an audio chunk using centrally managed Gemini credentials."""
    encoded_audio = payload.get("audio_base64")
    mime_type = payload.get("mime_type", "audio/wav")
    if not isinstance(encoded_audio, str) or len(encoded_audio) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio chunk is too large")
    if mime_type != "audio/wav":
        raise HTTPException(status_code=400, detail="Only audio/wav is supported")
    try:
        audio_bytes = base64.b64decode(encoded_audio, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid audio payload") from None
    if not audio_bytes or len(audio_bytes) > 18 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio chunk is empty or too large")

    from src.llm.gemini_client import transcribe_audio
    try:
        text = await run_in_threadpool(transcribe_audio, audio_bytes, mime_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="No active Gemini API key is configured") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Gemini transcription failed") from exc
    return {"text": text}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

