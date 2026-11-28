'use client'

import { useState, useEffect, useCallback } from 'react'
/* eslint-disable react-hooks/set-state-in-effect */
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { BookOpen, ClipboardCheck, Heart, MessageSquare } from 'lucide-react'
import { coursesApi, enrollmentsApi, sectionsApi, wishlistApi, type Course, type Enrollment, type Section } from '../../services/api'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Skeleton } from '../../components/ui/Skeleton'
import { ReviewSection } from './ReviewSection'
import { Announcements } from './Announcements'

const TRUSTED_PAYMENT_HOSTS = new Set([
  'sandbox.vnpay.vn',
  'sandbox.vnpayment.vn',
  'pay.vnpay.vn',
  'test-payment.momo.vn',
  'payment.momo.vn',
])

function getTrustedPaymentUrl(value: string): string | null {
  if (!value) return null
  if (value.startsWith('/')) return value
  try {
    const url = new URL(value)
    if (
      url.origin === window.location.origin ||
      url.hostname === 'localhost' ||
      url.hostname === '127.0.0.1' ||
      url.hostname === 'learninghubs.tech' ||
      (url.protocol === 'https:' && TRUSTED_PAYMENT_HOSTS.has(url.hostname))
    ) {
      return url.toString()
    }
    return null
  } catch {
    return null
  }
}

export function CourseDetail() {
  const params = useParams<{ id: string }>()
  const id = params?.id
  const router = useRouter()
  const [course, setCourse] = useState<Course | null>(null)
  const [sections, setSections] = useState<Section[]>([])
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null)
  const [loading, setLoading] = useState(true)
  const [enrolling, setEnrolling] = useState(false)
  const [isWishlisted, setIsWishlisted] = useState(false)

  const loadCourse = useCallback(async () => {
    if (!id) return
    setLoading(true)
    try {
      const [courseRes, enrollRes, wishRes] = await Promise.all([
        coursesApi.get(id),
        enrollmentsApi.list({ status: 'active' }).catch(() => ({ data: { items: [] } })),
        wishlistApi.check(id).catch(() => ({ data: { is_wishlisted: false } })),
      ])
      setCourse(courseRes.data)
      const userEnrollment = enrollRes.data.items.find((e: Enrollment) => e.course_id === id)
      setEnrollment(userEnrollment || null)
      if (userEnrollment) {
        const secRes = await sectionsApi.list(id).catch(() => ({ data: [] as Section[] }))
        setSections(secRes.data || [])
      } else {
        setSections([])
      }
      setIsWishlisted(wishRes.data.is_wishlisted)
    } catch (err) {
      console.error('Failed to load course:', err)
    } finally {
      setLoading(false)
    }
  }, [id])

  const toggleWishlist = async () => {
    if (!id) return
    try {
      if (isWishlisted) {
        await wishlistApi.remove(id)
        setIsWishlisted(false)
      } else {
        await wishlistApi.add(id)
        setIsWishlisted(true)
      }
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    loadCourse()
  }, [loadCourse])

  const handleEnroll = async (paymentMethod?: 'vnpay' | 'momo' | 'free') => {
    if (!id) return
    if (course?.price === 0) {
      paymentMethod = 'free'
    }
    setEnrolling(true)
    try {
      const res = await enrollmentsApi.enroll(id, paymentMethod)
      if (res.data.payment_url) {
        const paymentUrl = getTrustedPaymentUrl(res.data.payment_url)
        if (!paymentUrl) {
          throw new Error('Địa chỉ thanh toán không hợp lệ')
        }
        window.location.assign(paymentUrl)
      } else {
        router.push(`/app/student/courses/${id}/learn`)
      }
    } catch (err) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      const msg = axiosErr?.response?.data?.detail || 'Đăng ký thất bại'
      alert(msg)
    } finally {
      setEnrolling(false)
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    return `${mins} phút`
  }

  const getMaterialIcon = (type: string) => {
    switch (type) {
      case 'pdf': return '📄'
      case 'docx': return '📝'
      case 'video': return '🎬'
      case 'image': return '🖼️'
      case 'url': return '🔗'
      default: return '📎'
    }
  }

  const getMaterialDuration = (material: Course['materials'][0]) => {
    const meta = material.file_metadata || {}
    if (meta.duration_seconds) return formatDuration(meta.duration_seconds as number)
    if (meta.page_count) return `${meta.page_count as number} trang`
    if (material.file_size) return `${Math.round(material.file_size / 1024)} KB`
    return null
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-64 w-full" />
        <div className="space-y-4">
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-foreground">Không tìm thấy khóa học</h2>
        <Link href="/app/courses" className="text-primary hover:underline mt-2 block">
          Quay lại danh sách khóa học
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="aspect-video bg-gradient-to-br from-primary/5 to-accent/5 rounded-xl flex items-center justify-center overflow-hidden">
            {course.thumbnail_url ? (
              <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" />
            ) : (
              <span className="text-6xl">📚</span>
            )}
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              {course.category && (
                <Badge variant="primary" label={course.category.name} />
              )}
              <Badge variant={course.status === 'published' ? 'success' : 'warning'} label={course.status === 'published' ? 'Đang mở' : course.status} />
            </div>
            <h1 className="text-2xl md:text-3xl font-bold mb-4 text-foreground">{course.title}</h1>
            <div className="flex items-center gap-4 mb-6">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-lg font-medium text-primary">
                  {course.lecturer?.full_name?.[0] || 'L'}
                </div>
                <div>
                  <p className="font-medium text-foreground">{course.lecturer?.full_name || 'Giảng viên'}</p>
                  <p className="text-sm text-muted-foreground">{course.enrolled_count ?? course.enrollment_count ?? 0} học viên</p>
                </div>
              </div>
            </div>

            <div className="max-w-none">
              <h2 className="text-xl font-semibold mb-3 text-foreground">Mô tả khóa học</h2>
              <p className="text-muted-foreground whitespace-pre-wrap">{course.description}</p>
            </div>
          </div>

          <Announcements courseId={course.id} />

          <div>
            <h2 className="text-xl font-semibold mb-4 text-foreground">
              Nội dung khóa học ({sections.reduce((acc, s) => acc + (s.lessons?.length || s.lesson_count || 0), 0) || course.lesson_count || course.materials?.length || 0} bài)
            </h2>
            {sections.length > 0 && (
              <div className="space-y-3 mb-4">
                {sections.map((section, sIdx) => (
                  <Card key={section.id} padding="responsive" className="space-y-2">
                    <div className="font-semibold text-foreground">
                      Chương {sIdx + 1}: {section.title}
                    </div>
                    <div className="space-y-1.5 pl-2">
                      {(section.lessons || []).map((lesson, lIdx) => (
                        <div key={lesson.id} className="flex items-center justify-between gap-3 py-1.5 border-t border-border/50 first:border-t-0">
                          <span className="text-sm text-foreground/90 truncate">
                            {lIdx + 1}. {lesson.title}
                          </span>
                          {enrollment && (
                            <Link href={`/app/student/courses/${course.id}/learn`}>
                              <Button variant="ghost" size="sm">Học ngay</Button>
                            </Link>
                          )}
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            )}
            <div className="space-y-2">
              {course.materials?.map((material, index) => (
                <Card key={material.id} padding="responsive" className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm font-medium text-muted-foreground shrink-0">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-lg">{getMaterialIcon(material.material_type)}</span>
                      <span className="font-medium text-foreground truncate">{material.title}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {getMaterialDuration(material) || material.material_type.toUpperCase()}
                    </p>
                  </div>
                  {enrollment && (
                    <Link href={`/app/student/courses/${course.id}/learn?material=${material.id}`}>
                      <Button variant="ghost" size="sm">Học ngay</Button>
                    </Link>
                  )}
                </Card>
              ))}
            </div>
          </div>

          <ReviewSection courseId={course.id} />
        </div>

        <div className="space-y-4">
          <Card padding="responsive" className="lg:sticky lg:top-4">
            <div className="text-center mb-6">
                <div className="flex items-center justify-between">
                  {course.price === 0 ? (
                    <span className="text-3xl font-bold text-success">Miễn phí</span>
                  ) : (
                    <span className="text-3xl font-bold text-primary">
                      {new Intl.NumberFormat('vi-VN').format(course.price)}đ
                    </span>
                  )}
                  <button
                    onClick={toggleWishlist}
                    className="p-2 rounded-lg hover:bg-muted transition"
                    aria-label={isWishlisted ? 'Xóa khỏi danh sách yêu thích' : 'Thêm vào danh sách yêu thích'}
                  >
                    <Heart className={`h-5 w-5 ${isWishlisted ? 'fill-destructive text-destructive' : 'text-muted-foreground'}`} />
                  </button>
                </div>
            </div>

            {enrollment ? (
              <div className="space-y-3">
                <div className="text-center text-success font-medium mb-2">
                  ✓ Bạn đã đăng ký khóa học này
                </div>
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Tiến độ</span>
                    <span className="text-foreground font-medium">{enrollment.progress_percent || 0}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${enrollment.progress_percent || 0}%` }}
                    />
                  </div>
                </div>
                <Link href={`/app/student/courses/${course.id}/learn`} className="block">
                  <Button className="w-full">Tiếp tục học</Button>
                </Link>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
                  <Link href={`/app/student/courses/${course.id}/learn?tab=discussion`} className="block">
                    <Button variant="outline" className="w-full" icon={<MessageSquare className="h-4 w-4" />}>
                      Thảo luận khóa học
                    </Button>
                  </Link>
                  <Link href={`/app/student/courses/${course.id}/learn?tab=assignments`} className="block">
                    <Button variant="outline" className="w-full" icon={<ClipboardCheck className="h-4 w-4" />}>
                      Bài tập
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {course.price === 0 ? (
                  <Button
                    className="w-full"
                    size="lg"
                    onClick={() => handleEnroll()}
                    disabled={enrolling}
                  >
                    {enrolling ? 'Đang đăng ký...' : 'Đăng ký miễn phí'}
                  </Button>
                ) : (
                  <>
                    <Button
                      className="w-full"
                      size="lg"
                      onClick={() => handleEnroll('vnpay')}
                      disabled={enrolling}
                    >
                      Thanh toán qua VNPay
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full"
                      size="lg"
                      onClick={() => handleEnroll('momo')}
                      disabled={enrolling}
                    >
                      Thanh toán qua MoMo
                    </Button>
                    <p className="text-xs text-center text-muted-foreground mt-2">
                      Đăng ký = Thanh toán → Học ngay. Không hoàn tiền.
                    </p>
                  </>
                )}
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-border space-y-3 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <BookOpen className="h-4 w-4 shrink-0" />
                <span>{sections.reduce((acc, s) => acc + (s.lessons?.length || s.lesson_count || 0), 0) || course.lesson_count || course.materials?.length || 0} bài học</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span role="img" aria-label="students">👥</span>
                <span>{course.enrolled_count ?? course.enrollment_count ?? 0} học viên</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span role="img" aria-label="time">⏱️</span>
                <span>Học mọi lúc, mọi nơi</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span role="img" aria-label="unlimited">🔄</span>
                <span>Học lại không giới hạn</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
