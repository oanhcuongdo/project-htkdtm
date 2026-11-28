'use client'

import { useRouter } from 'next/navigation'
import { FileText, MessageSquare, Layers, PenLine, Settings, BookOpen, type LucideIcon } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'

export interface CommandItem {
  id: string
  label: string
  description?: string
  icon: LucideIcon
  group: string
  shortcut?: string
  action: () => void
}

export function useDefaultCommandItems(): CommandItem[] {
  const router = useRouter()
  const user = useAppStore((s) => s.auth.user)

  const items: CommandItem[] = [
    {
      id: 'nav-documents',
      label: 'Tài liệu',
      description: 'Tải lên và quản lý kho tri thức của bạn',
      icon: FileText,
      group: 'Điều hướng',
      shortcut: 'G D',
      action: () => router.push('/app/student/documents'),
    },
    {
      id: 'nav-chat',
      label: 'Trò chuyện AI',
      description: 'Hỏi đáp thông minh về tài liệu học tập',
      icon: MessageSquare,
      group: 'Điều hướng',
      shortcut: 'G C',
      action: () => router.push('/app/student/chat'),
    },
    {
      id: 'nav-quiz',
      label: 'Tạo đề trắc nghiệm AI',
      description: 'Tạo câu hỏi trắc nghiệm ôn luyện',
      icon: BookOpen,
      group: 'Công cụ học tập',
      action: () => router.push('/app/student/quiz'),
    },
    {
      id: 'nav-flashcards',
      label: 'Thẻ ghi nhớ Flashcards',
      description: 'Ghi nhớ ngắt quãng thông minh',
      icon: Layers,
      group: 'Công cụ học tập',
      action: () => router.push('/app/student/flashcards'),
    },
    {
      id: 'nav-essay',
      label: 'Chấm bài luận AI',
      description: 'Nhận đánh giá và gợi ý cải thiện bài viết',
      icon: PenLine,
      group: 'Công cụ học tập',
      action: () => router.push('/app/student/essay'),
    },
  ]

  if (user?.role === 'admin') {
    items.push({
      id: 'nav-admin',
      label: 'Bảng quản trị',
      description: 'Quản lý người dùng và trạng thái hệ thống',
      icon: Settings,
      group: 'Điều hướng',
      action: () => router.push('/app/admin'),
    })
  }

  return items
}
