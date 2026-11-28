import { redirect } from 'next/navigation'

export default function LegacyDocumentsRedirectPage() {
  redirect('/app/student/documents')
}
