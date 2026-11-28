from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations

from .cleaner import normalize_key


STOPWORDS = {"a", "an", "and", "for", "from", "in", "of", "on", "the", "to", "with", "course", "complete", "learn", "learning"}


def _title_tokens(record):
    return {token for token in normalize_key(record.get("title")).split() if len(token) > 2 and token not in STOPWORDS}


def deduplicate(records: list[dict]) -> tuple[list[dict], list[dict]]:
    exact_keys = set()
    canonical_urls = set()
    unique = []
    pairs = []
    for record in records:
        source_key = (record.get("source_name"), record.get("source_course_id"))
        url = record.get("canonical_url")
        exact = (source_key[0] and source_key[1] and source_key in exact_keys) or (url and url in canonical_urls)
        if exact:
            record["duplicate_status"] = "exact_duplicate"
        else:
            record["duplicate_status"] = "unique"
            unique.append(record)
            if source_key[0] and source_key[1]:
                exact_keys.add(source_key)
            if url:
                canonical_urls.add(url)

    postings = defaultdict(list)
    tokens_by_index = []
    for index, record in enumerate(unique):
        tokens = _title_tokens(record)
        tokens_by_index.append(tokens)
        for token in tokens:
            postings[token].append(index)
    candidate_pairs = set()
    for indexes in postings.values():
        if len(indexes) > 250:
            continue
        for left, right in combinations(indexes, 2):
            candidate_pairs.add((left, right))
    near_by_index = defaultdict(list)
    for left, right in candidate_pairs:
        a, b = unique[left], unique[right]
        if a.get("provider") and b.get("provider") and normalize_key(a["provider"]) != normalize_key(b["provider"]):
            continue
        ta, tb = tokens_by_index[left], tokens_by_index[right]
        union = ta | tb
        jaccard = len(ta & tb) / len(union) if union else 0
        sequence = SequenceMatcher(None, normalize_key(a.get("title")), normalize_key(b.get("title"))).ratio()
        score = max(jaccard, sequence)
        if score >= 0.9:
            pair = {"left_course_id": a.get("course_id"), "right_course_id": b.get("course_id"), "left_title": a.get("title"), "right_title": b.get("title"), "similarity": round(score, 4), "reason": "title similarity; manual review required"}
            pairs.append(pair)
            near_by_index[left].append(pair)
            near_by_index[right].append(pair)
    for index, record in enumerate(unique):
        if near_by_index[index]:
            record["duplicate_status"] = "near_duplicate"
            record.setdefault("quality_flags", []).append("near_duplicate_review")
    return records, pairs
