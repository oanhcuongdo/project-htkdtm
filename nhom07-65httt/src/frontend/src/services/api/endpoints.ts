import { api, getAccessToken } from './client'
import type { AuthUser, AuthResponse, DocumentItem, ChatSession, Citation, ChatMessage, ChatAskResponse, CourseChatMessage, SocialChatUser, SocialChatRoom, SocialChatMessage, Category, CourseMaterial, Course, Section, Lesson, Attachment, Quiz, Question, Answer, QuizAttempt, QuizStudent, QuizAttemptResult, WeaknessSummaryResponse, RemedialQuizResponse, LessonMindmapResponse, Assignment, AssignmentSubmission, Discussion, NotificationItem, WishlistItem, Announcement, Review, PaymentIntentResponse, Enrollment, MaterialProgressResponse, MaterialProgress, DashboardResponse, AudioSummaryResponse, AiApiKey, AiProviderSetting, CourseDiscussionItem, Note } from './types'

export const categoriesApi = {
  list: () => api.get<Category[]>('/categories'),
  get: (id: string) => api.get<Category>(`/categories/${id}`),
  getTree: () => api.get<Category[]>(`/categories/tree`),
  create: (data: { name: string; slug: string; description?: string; icon?: string; parent_id?: string | null }) =>
    api.post<Category>('/categories', data),
  update: (id: string, data: { name?: string; description?: string; icon?: string }) =>
    api.put<Category>(`/categories/${id}`, data),
  delete: (id: string) => api.delete(`/categories/${id}`),
}

export const coursesApi = {
  list: (params?: { category_id?: string; status?: string; page?: number; page_size?: number }) =>
    api.get<{ items: Course[]; total: number; page: number; page_size: number }>('/courses', { params }),
  get: (id: string) => api.get<Course>(`/courses/${id}`),
  create: (data: { title: string; description: string; price: number; category_id: string; thumbnail_url?: string }) =>
    api.post<Course>('/courses', data),
  listMyCourses: (params?: { page?: number; page_size?: number }) =>
    api.get<{ items: Course[]; total: number; page: number; page_size: number }>('/courses/lecturer', { params }),
  update: (id: string, data: Partial<Course>) => api.put<Course>(`/courses/${id}`, data),
  delete: (id: string) => api.delete(`/courses/${id}`),
  publish: (id: string) => api.post<Course>(`/courses/${id}/publish`, {}),
  archive: (id: string) => api.post<Course>(`/courses/${id}/archive`, {}),
  getMaterials: (id: string) => api.get<CourseMaterial[]>(`/courses/${id}/materials`),
  addMaterial: (id: string, data: FormData) =>
    // NOTE: do NOT set Content-Type manually — the browser must append the
    // multipart boundary itself. The request interceptor strips any stale
    // Content-Type when data is FormData (fixes "Missing boundary" 400s).
    api.post<CourseMaterial>(`/courses/${id}/materials`, data),
  updateMaterial: (courseId: string, materialId: string, data: Partial<CourseMaterial>) =>
    api.put<CourseMaterial>(`/courses/${courseId}/materials/${materialId}`, data),
  deleteMaterial: (courseId: string, materialId: string) =>
    api.delete(`/courses/${courseId}/materials/${materialId}`),
  reorderMaterials: (id: string, materialIds: string[]) =>
    api.put<CourseMaterial[]>(`/courses/${id}/materials/reorder`, { material_ids: materialIds }),
  // Lecturer dashboard
  getStats: () => api.get<{
    total_courses: number
    total_students: number
    total_revenue: number
    avg_rating: number
    recent_enrollments: { date: string; count: number }[]
    course_stats: { course_id: string; title: string; enrollment_count: number; revenue: number; rating_avg: number }[]
  }>('/courses/stats'),
  getReviews: (courseId: string, page = 1, pageSize = 20) =>
    api.get<{ items: Review[]; total: number }>(`/courses/${courseId}/reviews`, { params: { page, page_size: pageSize } }),
  createReview: (courseId: string, data: { rating: number; comment?: string }) =>
    api.post<Review>(`/courses/${courseId}/reviews`, data),
  getMyReview: (courseId: string) =>
    api.get<Review | null>(`/courses/${courseId}/reviews/my-review`),
  updateMyReview: (courseId: string, data: { rating?: number; comment?: string }) =>
    api.put<Review>(`/courses/${courseId}/reviews/my-review`, data),
  replyReview: (courseId: string, reviewId: string, reply: string) =>
    api.post<Review>(`/courses/${courseId}/reviews/${reviewId}/reply`, { reply }),
  getDiscussionStats: (courseId: string) =>
    api.get<{ total_discussions: number; unanswered: number }>(`/courses/${courseId}/discussions/stats`),
  getEnrolledStudents: (courseId: string) =>
    api.get<{ items: Enrollment[]; total: number }>(`/courses/${courseId}/enrolled-students`),
  getStudentProgressSummary: (courseId: string, studentId: string) =>
    api.get<{
      progress_percent: number
      lessons: Array<{ id: string; title: string; type: string; completed: boolean }>
      attempts: Array<{ id: string; quiz_id: string; title: string; score: number; max_score: number; passed: boolean; duration: string; date: string | null }>
    }>(`/courses/${courseId}/students/${studentId}/progress-summary`),
  sendStudentReminder: (courseId: string, studentId: string) =>
    api.post<{ status: string; message: string }>(`/courses/${courseId}/students/${studentId}/remind`),
  getQuizAnalytics: (courseId: string) =>
    api.get<Array<{ question: string; wrongRate: number; attempts: number }>>(`/courses/${courseId}/quiz-analytics`),
  aiAssist: (courseId: string, data: { topic: string; mode: 'outline' | 'summary' | 'transcript' }) =>
    api.post<{ output: string[] }>(`/courses/${courseId}/ai-assist`, data),
}

// ============ NEW LECTURER API ENDPOINTS ============

export const sectionsApi = {
  list: (courseId: string) => api.get<Section[]>(`/courses/${courseId}/sections`),
  get: (courseId: string, sectionId: string) => api.get<Section>(`/courses/${courseId}/sections/${sectionId}`),
  create: (courseId: string, data: { title: string; description?: string; order_index?: number }) =>
    api.post<Section>(`/courses/${courseId}/sections`, data),
  update: (courseId: string, sectionId: string, data: { title?: string; description?: string }) =>
    api.put<Section>(`/courses/${courseId}/sections/${sectionId}`, data),
  delete: (courseId: string, sectionId: string) => api.delete(`/courses/${courseId}/sections/${sectionId}`),
  reorder: (courseId: string, sectionIds: string[]) =>
    api.put<Section[]>(`/courses/${courseId}/sections/reorder`, { section_ids: sectionIds }),
}

export const lessonsApi = {
  list: (sectionId: string) => api.get<Lesson[]>(`/sections/${sectionId}/lessons`),
  get: (sectionId: string, lessonId: string) => api.get<Lesson>(`/sections/${sectionId}/lessons/${lessonId}`),
  create: (sectionId: string, data: {
    title: string
    description?: string
    type: 'VIDEO' | 'ARTICLE' | 'QUIZ' | 'ASSIGNMENT'
    video_url?: string
    video_duration?: number
    content?: string
    order_index?: number
    is_preview?: boolean
  }) => api.post<Lesson>(`/sections/${sectionId}/lessons`, data),
  update: (sectionId: string, lessonId: string, data: {
    title?: string
    description?: string
    video_url?: string
    video_duration?: number
    content?: string
    is_preview?: boolean
    is_active?: boolean
  }) => api.put<Lesson>(`/sections/${sectionId}/lessons/${lessonId}`, data),
  delete: (sectionId: string, lessonId: string) => api.delete(`/sections/${sectionId}/lessons/${lessonId}`),
  reorder: (sectionId: string, lessonIds: string[]) =>
    api.put<Lesson[]>(`/sections/${sectionId}/lessons/reorder`, { lesson_ids: lessonIds }),
  getAttachments: (sectionId: string, lessonId: string) => api.get<Attachment[]>(`/sections/${sectionId}/lessons/${lessonId}/attachments`),
  addAttachment: (sectionId: string, lessonId: string, data: FormData) =>
    // NOTE: do NOT set Content-Type manually — boundary is set by the browser.
    api.post<Attachment>(`/sections/${sectionId}/lessons/${lessonId}/attachments/upload`, data),
  deleteAttachment: (sectionId: string, lessonId: string, attachmentId: string) =>
    api.delete(`/sections/${sectionId}/lessons/${lessonId}/attachments/${attachmentId}`),
}

export const quizzesApi = {
  get: (lessonId: string) => api.get<Quiz>(`/lessons/${lessonId}/quiz`),
  create: (lessonId: string, data: {
    title: string
    description?: string
    passing_score?: number
    duration_mins?: number
    max_attempts?: number
  }) => api.post<Quiz>(`/lessons/${lessonId}/quiz`, data),
  update: (lessonId: string, data: {
    title?: string
    description?: string
    passing_score?: number
    duration_mins?: number
    max_attempts?: number
    is_active?: boolean
  }) => api.put<Quiz>(`/lessons/${lessonId}/quiz`, data),
  delete: (lessonId: string) => api.delete(`/lessons/${lessonId}/quiz`),
  getQuestions: (lessonId: string) => api.get<Question[]>(`/lessons/${lessonId}/quiz/questions`),
  addQuestion: (lessonId: string, data: {
    question_text: string
    type: 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'TRUE_FALSE' | 'FILL_BLANK'
    points?: number
    explanation?: string
    order_index?: number
    answers: { answer_text: string; is_correct: boolean }[]
  }) => api.post<Question>(`/lessons/${lessonId}/quiz/questions`, data),
  updateQuestion: (lessonId: string, questionId: string, data: {
    question_text?: string
    type?: 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'TRUE_FALSE' | 'FILL_BLANK'
    points?: number
    explanation?: string
  }) => api.put<Question>(`/lessons/${lessonId}/quiz/questions/${questionId}`, data),
  deleteQuestion: (lessonId: string, questionId: string) => api.delete(`/lessons/${lessonId}/quiz/questions/${questionId}`),
  reorderQuestions: (lessonId: string, questionIds: string[]) =>
    api.put<Question[]>(`/lessons/${lessonId}/quiz/questions/reorder`, { question_ids: questionIds }),
  updateAnswers: (lessonId: string, questionId: string, answers: { id?: string; answer_text: string; is_correct: boolean }[]) =>
    api.put<Answer[]>(`/lessons/${lessonId}/quiz/questions/${questionId}/answers`, { answers }),
  getAttempts: (lessonId: string) => api.get<QuizAttempt[]>(`/lessons/${lessonId}/quiz/attempts`),
  generateQuizAI: (lessonId: string, questionCount: number = 5) =>
    api.post<Quiz>(`/lessons/${lessonId}/quiz/generate-ai`, null, { params: { question_count: questionCount } }),
  // --- Student quiz flow (lecture-attached quiz) ---
  getStudentQuiz: (lessonId: string) => api.get<QuizStudent>(`/lessons/${lessonId}/quiz`),
  startAttempt: (lessonId: string) => api.post<QuizAttempt>(`/lessons/${lessonId}/quiz/attempt`),
  submitAttempt: (lessonId: string, attemptId: string, answers: Array<{ question_id: string; selected_answers: string[] }>) =>
    api.put<QuizAttemptResult>(`/lessons/${lessonId}/quiz/attempt/${attemptId}/submit`, { answers }),
  getMyAttempts: (lessonId: string) => api.get<QuizAttempt[]>(`/lessons/${lessonId}/quiz/my-attempts`),
}

export const adaptiveApi = {
  getMyWeaknesses: (limit: number = 5) =>
    api.get<WeaknessSummaryResponse>('/adaptive/my-weaknesses', { params: { limit } }),
  generateRemedialQuiz: (lessonId: string, questionCount: number = 3) =>
    api.post<RemedialQuizResponse>(`/adaptive/lessons/${lessonId}/remedial-quiz`, {
      question_count: questionCount,
    }),
}

export const mindmapApi = {
  getLessonMindmap: (lessonId: string) =>
    api.get<LessonMindmapResponse>(`/lessons/${lessonId}/mindmap`),
  regenerateLessonMindmap: (lessonId: string) =>
    api.post<LessonMindmapResponse>(`/lessons/${lessonId}/mindmap/regenerate`, {}),
  generateTextMindmap: (content: string, title?: string) =>
    api.post<{ markdown_tree: string }>('/study/mindmap/generate', { content, title: title || '' }),
}

export const audioApi = {
  getLessonAudioSummary: (lessonId: string, voice: 'female' | 'male' = 'female', regenerate: boolean = false) =>
    api.get<AudioSummaryResponse>(`/lessons/${lessonId}/audio-summary`, {
      params: { voice, regenerate },
    }),
}

export const assignmentsApi = {
  get: (lessonId: string) => api.get<Assignment | null>(`/lessons/${lessonId}/assignment`),
  create: (lessonId: string, data: {
    title: string
    description?: string
    instructions?: string
    deadline?: string
    max_score?: number
    allow_resubmit?: boolean
    max_resubmits?: number
  }) => api.post<Assignment>(`/lessons/${lessonId}/assignment`, data),
  update: (lessonId: string, data: {
    title?: string
    description?: string
    instructions?: string
    deadline?: string
    max_score?: number
    allow_resubmit?: boolean
    max_resubmits?: number
    is_active?: boolean
  }) => api.put<Assignment>(`/lessons/${lessonId}/assignment`, data),
  delete: (lessonId: string) => api.delete(`/lessons/${lessonId}/assignment`),
  submit: (lessonId: string, data: { submission_text?: string; attachments?: Record<string, unknown>[] }) =>
    api.post<AssignmentSubmission>(`/lessons/${lessonId}/assignment/submissions`, data),
  uploadSubmissionFile: (lessonId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{
      file_name: string
      file_url: string
      file_type: string
      file_size: number
      storage_key: string
    }>(`/lessons/${lessonId}/assignment/submissions/upload`, formData)
  },
  getMySubmissions: (lessonId: string) =>
    api.get<AssignmentSubmission[]>(`/lessons/${lessonId}/assignment/submissions`),
  getAllSubmissions: (lessonId: string) =>
    api.get<AssignmentSubmission[]>(`/lessons/${lessonId}/assignment/submissions/all`),
  gradeSubmission: (lessonId: string, submissionId: string, data: { score: number; feedback?: string }) =>
    api.post<AssignmentSubmission>(`/lessons/${lessonId}/assignment/submissions/${submissionId}/grade`, data),
}

export const discussionsApi = {
  list: (lessonId: string, page = 1, pageSize = 20) =>
    api.get<Discussion[] | { items: Discussion[]; total: number }>(`/lessons/${lessonId}/discussions`, {
      params: { page, page_size: pageSize },
    }),
  create: (lessonId: string, data: { content: string; parent_id?: string }) =>
    api.post<Discussion>(`/lessons/${lessonId}/discussions`, data),
  update: (discussionId: string, data: { content: string }, lessonId?: string) =>
    lessonId
      ? api.put<Discussion>(`/lessons/${lessonId}/discussions/posts/${discussionId}`, data)
      : api.put<Discussion>(`/discussions/${discussionId}`, data),
  delete: (discussionId: string, lessonId?: string) =>
    lessonId
      ? api.delete(`/lessons/${lessonId}/discussions/posts/${discussionId}`)
      : api.delete(`/discussions/${discussionId}`),
  upvote: (discussionId: string, lessonId?: string) =>
    lessonId
      ? api.post<Discussion | { upvotes: number }>(`/lessons/${lessonId}/discussions/posts/${discussionId}/upvote`)
      : api.post<{ upvotes: number }>(`/discussions/${discussionId}/upvote`),
  pin: (discussionId: string, lessonId?: string) =>
    lessonId
      ? api.post<Discussion>(`/lessons/${lessonId}/discussions/posts/${discussionId}/pin`, {})
      : api.post<Discussion>(`/discussions/${discussionId}/pin`, {}),
  markAsAnswer: (discussionId: string, lessonId?: string) =>
    lessonId
      ? api.post<Discussion>(`/lessons/${lessonId}/discussions/posts/${discussionId}/mark-answer`, {})
      : api.post<Discussion>(`/discussions/${discussionId}/mark-answer`, {}),
  listByCourse: (courseId: string) =>
    api.get<CourseDiscussionItem[]>(`/courses/${courseId}/discussions`),
  markAnswer: (lessonId: string, postId: string) =>
    api.post<Discussion>(`/lessons/${lessonId}/discussions/posts/${postId}/mark-answer`),
}

export const enrollmentsApi = {
  list: (params?: { status?: string; page?: number; page_size?: number }) =>
    api.get<{ items: Enrollment[]; total: number }>('/my-enrollments', { params }),
  get: (id: string) => api.get<Enrollment>(`/enrollments/${id}`),
  enroll: (courseId: string, paymentMethod?: 'vnpay' | 'momo' | 'free') =>
    api.post<PaymentIntentResponse>(`/courses/${courseId}/enroll/payment-intent`, {
      payment_method: paymentMethod,
    }),
  cancel: (id: string) => api.delete(`/enrollments/${id}`),
  getProgress: (id: string) =>
    api.get<{
      enrollment_id: string
      course_id: string
      total_materials: number
      completed_materials: number
      total_lessons: number
      completed_lessons: number
      completed_lesson_ids: string[]
      completion_percent: number
      materials: MaterialProgressResponse[]
    }>(`/enrollments/${id}/progress`),
  updateProgress: (enrollmentId: string, materialId: string, data: {
    completion_percent?: number
    last_position?: Record<string, unknown>
  }) => api.post<MaterialProgress>(`/enrollments/${enrollmentId}/materials/${materialId}/progress`, data),
  updateLessonProgress: (enrollmentId: string, lessonId: string, completed: boolean) =>
    api.post<{ id: string; enrollment_id: string; lesson_id: string; completed: boolean }>(
      `/enrollments/${enrollmentId}/lessons/${lessonId}/progress`,
      { completed }
    ),
}

export const paymentsApi = {
  getStatus: (paymentId: string) => api.get<{ status: string; enrollment_id?: string; course_id?: string }>(`/payments/${paymentId}/status`),
  mockConfirm: (data: { transaction_id: string; action: 'success' | 'cancel' | 'fail'; mock_token: string }) =>
    api.post<{ success: boolean; status: string; course_id?: string }>('/payments/mock/confirm', data),
  createVNPayUrl: (enrollmentId: string, amount: number) =>
    api.post<{ payment_url: string }>('/payments/vnpay/create', { enrollment_id: enrollmentId, amount }),
  createMoMoUrl: (enrollmentId: string, amount: number) =>
    api.post<{ payment_url: string }>('/payments/momo/create', { enrollment_id: enrollmentId, amount }),
}

export const dashboardApi = {
  getMyDashboard: () => api.get<DashboardResponse>('/dashboard/my-dashboard'),
}

export const authApi = {
  register: (data: { email: string; password: string; full_name?: string; role?: string }) =>
    api.post<AuthResponse>('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', data),
  googleLogin: (idToken: string) =>
    api.post<AuthResponse>('/auth/google', { id_token: idToken }),
  facebookLogin: (accessToken: string) =>
    api.post<AuthResponse>('/auth/facebook', { access_token: accessToken }),
  refresh: () =>
    api.post<{ access_token: string; refresh_token: string | null }>('/auth/refresh', {}),
  me: () => api.get<AuthUser>('/auth/me'),
  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    api.put<AuthUser>('/auth/me', data),
  forgotPassword: (email: string) =>
    api.post<{ message: string }>('/auth/forgot-password', { email }),
  resetPassword: (token: string, password: string) =>
    api.post<{ message: string }>('/auth/reset-password', { token, password }),
  changePassword: (current_password: string, new_password: string) =>
    api.post<{ message: string }>('/auth/change-password', { current_password, new_password }),
  logout: () =>
    api.post<{ message: string }>('/auth/logout', {}),
}

export const documentsApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<{ items: DocumentItem[]; total: number; page: number; page_size: number }>(
      '/documents/', { params: { page, page_size: pageSize } }
    ),
  get: (id: string) => api.get<DocumentItem>(`/documents/${id}`),
  upload: (file: File, title?: string, onUploadProgress?: (percent: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)
    // NOTE: do NOT set Content-Type manually — the browser must append the
    // multipart boundary itself (fixes "Missing boundary in multipart." 400s).
    // The request interceptor also strips any stale Content-Type for FormData.
    return api.post('/documents/upload', formData, {
      onUploadProgress: onUploadProgress
        ? (e) => {
            if (e.total) onUploadProgress(Math.round((e.loaded * 100) / e.total))
          }
        : undefined,
    })
  },
  retry: (id: string) => api.post<DocumentItem>(`/documents/${id}/retry`),
  delete: (id: string) => api.delete(`/documents/${id}`),
  getContentBlob: async (id: string, signal?: AbortSignal): Promise<Blob> => {
    const res = await api.get<Blob>(`/documents/${id}/content`, {
      responseType: 'blob',
      signal,
    })
    return res.data
  },
}

export const chatApi = {
  createSession: (data?: { course_id?: string; lesson_id?: string; title?: string }) =>
    api.post<ChatSession>('/chat/sessions', data),
  listSessions: (page = 1, pageSize = 20) =>
    api.get<{ items: ChatSession[]; total: number }>('/chat/sessions', {
      params: { page, page_size: pageSize },
    }),
  deleteSession: (id: string) => api.delete(`/chat/sessions/${id}`),
  ask: (data: { session_id: string; query: string; course_id?: string; lesson_id?: string; document_ids?: string[]; tutor_mode?: string; course_title?: string; strict_course?: boolean }) =>
    api.post<ChatAskResponse>('/chat/ask', data),
  askStream: async (
    data: { session_id: string; query: string; course_id?: string; lesson_id?: string; document_ids?: string[]; tutor_mode?: string; course_title?: string; strict_course?: boolean },
    onToken: (text: string) => void,
    onMeta?: (meta: { intent?: string; citations?: Citation[] }) => void,
    signal?: AbortSignal,
  ): Promise<{ answer: string; citations: Citation[] }> => {
    const base = (api.defaults.baseURL || '').replace(/\/+$/, '')
    const url = `${base}/chat/ask/stream`
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const accessToken = getAccessToken()
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`
    }
    const resp = await fetch(url, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify(data),
      signal,
    })
    if (!resp.ok || !resp.body) {
      throw new Error(`Stream request failed: ${resp.status}`)
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullAnswer = ''
    let citations: Citation[] = []

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''
      for (const evt of events) {
        const line = evt.trim()
        if (!line.startsWith('data: ')) continue
        try {
          const payload = JSON.parse(line.slice(6)) as
            | { type: 'token'; text: string }
            | { type: 'meta'; intent?: string; citations?: Citation[] }
            | { type: 'done'; answer: string }
            | { type: 'error'; message: string }
          if (payload.type === 'token') {
            fullAnswer += payload.text
            onToken(payload.text)
          } else if (payload.type === 'meta') {
            citations = payload.citations || []
            onMeta?.({ intent: payload.intent, citations })
          } else if (payload.type === 'done') {
            fullAnswer = payload.answer || fullAnswer
          } else if (payload.type === 'error') {
            throw new Error(payload.message || 'Stream error')
          }
        } catch (e) {
          if (e instanceof Error && e.message !== 'Stream error' && !(e instanceof SyntaxError)) throw e
          if (e instanceof Error && !e.message.includes('JSON')) throw e
        }
      }
    }
    return { answer: fullAnswer, citations }
  },
  listMessages: (sessionId: string, page = 1, pageSize = 50) =>
    api.get<{ items: ChatMessage[]; total: number }>(`/chat/sessions/${sessionId}/messages`, {
      params: { page, page_size: pageSize },
    }),
}

export const courseChatApi = {
  listMessages: (courseId: string, limit = 50, before?: string) =>
    api.get<{ items: CourseChatMessage[]; total: number }>(`/courses/${courseId}/chat/messages`, {
      params: { limit, before },
    }),
  sendMessage: (courseId: string, content: string) =>
    api.post<CourseChatMessage>(`/courses/${courseId}/chat/messages`, { content }),
}

export const socialChatApi = {
  searchUsers: (q = '', limit = 20) =>
    api.get<SocialChatUser[]>('/social-chat/users', { params: { q, limit } }),
  listRooms: () =>
    api.get<{ items: SocialChatRoom[]; total: number }>('/social-chat/rooms'),
  createRoom: (data: { name: string; description?: string; member_ids?: string[] }) =>
    api.post<SocialChatRoom>('/social-chat/rooms', data),
  directMessage: (otherUserId: string) =>
    api.post<SocialChatRoom>(`/social-chat/direct/${otherUserId}`),
  listMessages: (roomId: string, limit = 50, before?: string) =>
    api.get<{ items: SocialChatMessage[]; total: number }>(`/social-chat/rooms/${roomId}/messages`, {
      params: { limit, before },
    }),
  sendMessage: (roomId: string, content: string) =>
    api.post<SocialChatMessage>(`/social-chat/rooms/${roomId}/messages`, { content }),
}

export const studyApi = {
  generateQuiz: (data: { document_id: string; quiz_type?: string; question_count?: number }) =>
    api.post('/study/quiz/generate', data),
  getQuizJob: (jobId: string) => api.get(`/study/quiz/job/${jobId}`),
  listQuizHistory: (params?: { document_id?: string; page?: number; page_size?: number }) =>
    api.get('/study/quiz/history', { params }),
  getQuizSet: (id: string) => api.get(`/study/quiz/sets/${id}`),
  deleteQuizSet: (id: string) => api.delete(`/study/quiz/sets/${id}`),
  submitQuiz: (quizId: string, answers: Array<{ question_id: string; answer: string }>) =>
    api.post(`/study/quiz/${quizId}/submit`, { answers }),
  generateCourseQuiz: (data: { course_id: string; question_count: number; lesson_ids?: string[] }) =>
    api.post<{ job_id: string; status: string }>('/study/quiz/by-course', data),
  generateFlashcards: (data: { document_id: string; set_name: string; count?: number }) =>
    api.post('/study/flashcards/generate', data),
  getFlashcard: (id: string) => api.get(`/study/flashcards/${id}`),
  listFlashcards: (params?: { document_id?: string; page?: number; page_size?: number }) =>
    api.get('/study/flashcards', { params }),
  deleteFlashcard: (id: string) => api.delete(`/study/flashcards/${id}`),
  submitEssay: (data: { document_id: string; essay_text: string }) =>
    api.post<{ job_id: string; status: string }>('/study/essay/submit', data),
  getEssayJob: (jobId: string) => api.get(`/study/essay/job/${jobId}`),
}

export const adminApi = {
  listUsers: (page = 1, pageSize = 20) =>
    api.get('/admin/users', { params: { page, page_size: pageSize } }),
  createUser: (data: { email: string; password: string; full_name?: string; role: string }) =>
    api.post('/admin/users', data),
  updateUser: (userId: string, data: { full_name?: string; role?: string; is_active?: boolean }) =>
    api.put(`/admin/users/${userId}`, data),
  deleteUser: (userId: string) =>
    api.delete(`/admin/users/${userId}`),
  listAllCourses: (params?: { page?: number; page_size?: number; search?: string; status?: string }) =>
    api.get('/admin/courses', { params }),
  deleteCourse: (courseId: string) =>
    api.delete(`/admin/courses/${courseId}`),
  analytics: () => api.get('/admin/analytics'),
  health: () => api.get('/admin/health'),
  listAiKeys: (provider?: string) =>
    api.get<{ items: AiApiKey[]; total: number }>('/admin/ai-keys', { params: provider ? { provider } : undefined }),
  getAiSettings: () => api.get<AiProviderSetting>('/admin/ai-settings'),
  updateAiSettings: (data: { model_id: string }) => api.put<AiProviderSetting>('/admin/ai-settings', data),
  createAiKey: (data: { api_key: string; key_name: string; provider?: string }) =>
    api.post<AiApiKey>('/admin/ai-keys', data),
  deleteAiKey: (id: string) => api.delete(`/admin/ai-keys/${id}`),
  toggleAiKey: (id: string) => api.patch<AiApiKey>(`/admin/ai-keys/${id}/toggle`, {}),
}

export const notificationsApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<{ items: NotificationItem[]; total: number; unread_count: number }>('/notifications', { params: { page, page_size: pageSize } }),
  markRead: (id: string) => api.put<NotificationItem>(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
  delete: (id: string) => api.delete(`/notifications/${id}`),
}

export const wishlistApi = {
  list: () => api.get<WishlistItem[]>('/wishlist'),
  add: (courseId: string) => api.post<WishlistItem>(`/wishlist/${courseId}`),
  remove: (courseId: string) => api.delete(`/wishlist/${courseId}`),
  check: (courseId: string) => api.get<{ is_wishlisted: boolean }>(`/wishlist/check/${courseId}`),
}

export const announcementsApi = {
  list: (courseId: string) => api.get<Announcement[]>(`/courses/${courseId}/announcements`),
  create: (courseId: string, data: { title: string; content: string }) =>
    api.post<Announcement>(`/courses/${courseId}/announcements`, data),
  delete: (courseId: string, id: string) =>
    api.delete(`/courses/${courseId}/announcements/${id}`),
}

export const notesApi = {
  list: (params: { course_id: string; lesson_id?: string }) =>
    api.get<Note[]>('/notes', { params }),
  create: (data: { course_id: string; lesson_id?: string; content: string }) =>
    api.post<Note>('/notes', data),
  update: (id: string, data: { content: string }) =>
    api.put<Note>(`/notes/${id}`, data),
  delete: (id: string) => api.delete(`/notes/${id}`),
}
