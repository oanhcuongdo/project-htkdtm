import { Suspense } from 'react'
import { CourseLearning } from '@/features/courses/CourseLearning'

export default function StudentCourseLearnRoutePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <CourseLearning />
    </Suspense>
  )
}
