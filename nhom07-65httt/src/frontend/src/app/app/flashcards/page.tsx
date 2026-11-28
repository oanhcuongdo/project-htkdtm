import { redirect } from 'next/navigation'

export default function LegacyFlashcardsRedirectPage() {
  redirect('/app/student/flashcards')
}
