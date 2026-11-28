import { redirect } from 'next/navigation'

export default function LegacyCoursesRedirectPage() {
  redirect('/app/student/courses')
}
