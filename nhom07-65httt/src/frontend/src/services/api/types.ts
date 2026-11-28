export interface AuthUser {
  id: string
  email: string
  full_name: string | null
  avatar_url: string | null
  role: string
  created_at: string | null
  quota?: {
    storage_limit_mb: number
    storage_used_mb: number
    video_limit: number
    video_used: number
    token_limit: number
    token_used: number
  }
}

export interface AuthResponse {
  user: AuthUser
  token: { access_token: string; token_type: string; refresh_token: string | null }
}

export interface DocumentItem {
  id: string
  file_name: string
  file_type: string
  file_url: string
  file_size: number | null
  status: string
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ChatSession {
  id: string
  title: string | null
  course_id: string | null
  lesson_id: string | null
  context_type: string
  created_at: string
  updated_at: string
}

export interface Citation {
  document_id: string
  chunk_id: string
  page_number: number | null
  text: string
  course_id?: string
  lesson_id?: string
  material_id?: string
}

export interface ChatMessage {
  id: string
  role: string
  content: string
  citations: Citation[] | null
  created_at: string
}

export interface ChatAskResponse {
  answer: string
  citations: Citation[]
  token_usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
}

export interface CourseChatMessage {
  id: string
  course_id: string
  sender_id: string
  sender_name: string | null
  sender_role: string
  content: string
  created_at: string
}

export interface SocialChatUser {
  id: string
  full_name: string | null
  email: string
  avatar_url: string | null
  role: string
}

export interface SocialChatRoom {
  id: string
  name: string
  description: string | null
  kind: 'group' | 'direct'
  member_count: number
  last_message: string | null
  updated_at: string
}

export interface SocialChatMessage {
  id: string
  room_id: string
  sender_id: string
  sender_name: string | null
  sender_avatar_url: string | null
  sender_role: string
  content: string
  created_at: string
}

export interface Category {
  id: string
  name: string
  description: string | null
  icon: string | null
  course_count: number
}

export interface CourseMaterial {
  id: string
  file_name: string | null
  title: string | null
  material_type: string
  file_type: string
  file_url: string | null
  external_url: string | null
  file_size: number | null
  status: string
  is_indexed: boolean
  file_metadata: Record<string, unknown> | null
  course_id: string
  lecturer_id: string
  created_at: string
  updated_at: string
}

export interface Course {
  id: string
  title: string
  description: string
  thumbnail_url: string | null
  price: number
  category_id: string
  category?: Category
  lecturer_id: string
  lecturer?: { id: string; full_name: string | null; avatar_url: string | null }
  status: 'draft' | 'published' | 'archived'
  level: string
  language: string
  requirements: string | null
  learning_outcomes: string | null
  tags: string | null
  view_count: number
  rating_avg: number
  rating_count: number
  enrollment_count: number
  enrolled_count?: number
  lesson_count?: number
  materials: CourseMaterial[]
  created_at: string
  updated_at: string
}

// ============ NEW LMS TYPES ============

export interface Section {
  id: string
  course_id: string
  title: string
  description: string | null
  order_index: number
  created_at: string
  updated_at: string
  lesson_count?: number
  lessons?: Lesson[]
}

export interface Lesson {
  id: string
  section_id: string
  title: string
  description: string | null
  type: 'VIDEO' | 'ARTICLE' | 'QUIZ' | 'ASSIGNMENT'
  video_url: string | null
  video_duration: number | null
  content: string | null
  order_index: number
  is_preview: boolean
  is_active: boolean
  has_quiz: boolean
  has_assignment: boolean
  attachment_count: number
  created_at: string
  updated_at: string
  quiz?: Quiz
  assignment?: Assignment
  attachments?: Attachment[]
}

export interface Attachment {
  id: string
  lesson_id: string
  file_name: string
  file_url: string
  file_type: string | null
  file_size: number | null
  uploaded_at: string
}

export interface Quiz {
  id: string
  lesson_id: string
  title: string
  description: string | null
  passing_score: number
  duration_mins: number | null
  max_attempts: number
  is_active: boolean
  question_count?: number
  created_at: string
  updated_at: string
  questions?: Question[]
}

export interface Question {
  id: string
  quiz_id: string
  question_text: string
  type: 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'TRUE_FALSE' | 'FILL_BLANK'
  points: number
  explanation: string | null
  order_index: number
  created_at: string
  answers?: Answer[]
}

export interface Answer {
  id: string
  question_id: string
  answer_text: string
  is_correct: boolean
  order_index: number
  created_at: string
}

export interface QuizAttempt {
  id: string
  enrollment_id: string
  quiz_id: string
  attempt_number: number
  score: number | null
  max_score: number | null
  passed: boolean | null
  answers_detail?: Array<{
    question_id: string
    question_text?: string
    question_type?: string
    points?: number
    earned_points?: number
    is_correct: boolean
    selected_answers?: string[]
    correct_answers?: string[]
    explanation?: string | null
  }> | null
  started_at: string
  completed_at: string | null
}

export interface AnswerStudent {
  id: string
  question_id: string
  answer_text: string
  order_index: number
  created_at: string
}

export interface QuestionStudent {
  id: string
  quiz_id: string
  question_text: string
  type: 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'TRUE_FALSE' | 'FILL_BLANK'
  points: number
  order_index: number
  created_at: string
  answers?: AnswerStudent[]
}

export interface QuizStudent {
  id: string
  lesson_id: string
  title: string
  description: string | null
  passing_score: number
  duration_mins: number | null
  max_attempts: number
  is_active: boolean
  question_count?: number
  created_at: string
  updated_at: string
  questions?: QuestionStudent[]
}

export interface QuizAttemptResult extends QuizAttempt {
  correct_answers?: Array<Record<string, unknown>>
}

export interface MissedQuestionItem {
  question_id: string
  question_text: string
  selected_answers: string[]
  correct_answers: string[]
  explanation?: string | null
  is_correct?: boolean
}

export interface WeaknessAreaItem {
  lesson_id: string
  lesson_title: string
  course_id: string
  course_title: string
  total_questions: number
  missed_count: number
  accuracy_percent: number
  last_attempt_at?: string | null
  missed_questions: MissedQuestionItem[]
}

export interface WeaknessSummaryResponse {
  weaknesses: WeaknessAreaItem[]
  total_weak_areas: number
}

export interface RemedialQuestion {
  id: string
  question: string
  options: string[]
  correct_answer: string
  explanation?: string | null
}

export interface RemedialQuizResponse {
  lesson_id: string
  lesson_title: string
  target_weaknesses_count: number
  questions: RemedialQuestion[]
}

export interface LessonMindmapResponse {
  lesson_id: string
  lesson_title: string
  markdown_tree: string
  is_cached: boolean
}

export interface Assignment {
  id: string
  lesson_id: string
  title: string
  description: string | null
  instructions: string | null
  deadline: string | null
  max_score: number
  allow_resubmit: boolean
  max_resubmits: number
  is_active: boolean
  submission_count?: number
  created_at: string
  updated_at: string
}

export interface AssignmentSubmission {
  id: string
  assignment_id: string
  student_id: string
  student_name: string | null
  submission_text: string | null
  attachments: { file_name: string; file_url: string }[] | null
  score: number | null
  feedback: string | null
  submitted_at: string
  graded_at: string | null
  is_late: boolean
}

export interface Discussion {
  id: string
  lesson_id: string
  user_id: string
  user_name: string | null
  user_avatar: string | null
  parent_id: string | null
  content: string
  is_pinned: boolean
  is_answer: boolean
  upvotes: number
  reply_count: number
  created_at: string
  updated_at: string
  replies: Discussion[]
}

export interface NotificationItem {
  id: string
  user_id: string
  title: string
  detail: string | null
  type: string
  related_id: string | null
  related_type: string | null
  is_read: boolean
  created_at: string
}

export interface WishlistItem {
  id: string
  user_id: string
  course_id: string
  course_title: string | null
  course_thumbnail: string | null
  course_price: number | null
  created_at: string
}

export interface Announcement {
  id: string
  course_id: string
  lecturer_id: string
  lecturer_name: string | null
  title: string
  content: string
  created_at: string
  updated_at: string
}

export interface Review {
  id: string
  enrollment_id: string
  rating: number
  comment: string | null
  lecturer_reply: string | null
  replied_at: string | null
  created_at: string
  student_name: string | null
  course_title: string | null
}

export interface PaymentIntentResponse {
  payment_url: string
  transaction_id: string
  amount_vnd: number
}

export interface Enrollment {
  id: string
  user_id: string
  student_id?: string
  course_id: string
  course?: Course
  enrolled_at: string
  completed_at: string | null
  progress_percent: number
  status: 'active' | 'completed' | 'cancelled'
  payment_id: string | null
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded'
  payment_amount_vnd?: number
  payment_method?: string | null
  course_title?: string | null
  course_thumbnail?: string | null
  lecturer_name?: string | null
  student_name?: string | null
  student_email?: string | null
  student_avatar_url?: string | null
}

export interface MaterialProgressResponse {
  id: string
  enrollment_id: string
  material_id: string
  completion_percent: number
  completed: boolean
  last_position: Record<string, unknown> | null
  completed_at: string | null
}

export interface MaterialProgress {
  id: string
  enrollment_id: string
  material_id: string
  completion_percent: number
  completed: boolean
  last_position: Record<string, unknown> | null
  completed_at: string | null
}

export interface DashboardCourseProgress {
  id: string
  course_id: string
  course_title: string
  course_thumbnail: string | null
  lecturer_name: string | null
  enrolled_at: string
  completion_percent: number
  total_materials: number
  completed_materials: number
}

export interface DashboardStats {
  total_enrolled: number
  total_materials: number
  total_completed: number
  avg_progress: number
  streak_days?: number
  daily_goal_percent?: number
}

export interface DashboardActivity {
  id: string
  activity_type: string
  title: string
  score: number | null
  created_at: string
}

export interface DashboardResponse {
  courses: DashboardCourseProgress[]
  stats: DashboardStats
  recent_activity: DashboardActivity[]
}

export interface AudioSummaryResponse {
  lesson_id: string
  lesson_title: string
  audio_url: string
  voice: string
  is_cached: boolean
}

export interface AiApiKey {
  id: string
  provider: string
  key_name: string
  masked_key: string
  is_active: boolean
  usage_count: number
  last_used_at: string | null
  created_at: string | null
}

export interface AiProviderSetting {
  provider: string
  model_id: string
  updated_at: string
  synced?: boolean
}

export interface CourseDiscussionItem {
  id: string
  lesson_id: string
  lesson_title?: string
  user_id: string
  user_name?: string
  user_avatar?: string
  content: string
  is_pinned: boolean
  is_answer: boolean
  upvotes: number
  reply_count: number
  created_at: string
  updated_at: string
}

export interface Note {
  id: string
  user_id: string
  course_id: string
  lesson_id: string | null
  content: string
  created_at: string
  updated_at: string
}
