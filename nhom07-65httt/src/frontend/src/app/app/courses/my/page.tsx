import { redirect } from 'next/navigation'

export default function LegacyMyCoursesRedirectPage() {
  redirect('/app/student/courses')
}
