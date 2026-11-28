'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Database,
  Bot,
  Zap,
  Shield,
  HardDrive,
  Activity,
  Key,
} from 'lucide-react'
import { adminApi } from '../../services/api'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { useToast } from '../../components/ui/useToast'

interface HealthData {
  status: string
  services: {
    database: string
    ai_service: string
    redis: string
    s3_storage: string
    qdrant: string
    celery: string
  }
}

export function AdminSettings() {
  const router = useRouter()
  const toast = useToast()
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchHealth = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminApi.health()
      setHealth(res.data)
    } catch {
      toast({ type: 'error', title: 'Không thể tải trạng thái dịch vụ hệ thống' })
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    let ignore = false
    adminApi.health()
      .then((res) => {
        if (!ignore) setHealth(res.data)
      })
      .catch(() => {
        if (!ignore) toast({ type: 'error', title: 'Không thể tải trạng thái dịch vụ hệ thống' })
      })

    return () => {
      ignore = true
    }
  }, [toast])

  const services = [
    { name: 'Cơ sở dữ liệu PostgreSQL', description: 'Lưu trữ dữ liệu quan hệ', icon: Database, key: 'database' as const },
    { name: 'Dịch vụ AI LangGraph', description: 'Công cụ điều phối luồng LLM', icon: Bot, key: 'ai_service' as const },
    { name: 'Bộ nhớ đệm Redis (Upstash)', description: 'Bộ đệm phiên và truy vấn', icon: Zap, key: 'redis' as const },
    { name: 'Kho lưu trữ Cloudflare R2', description: 'Lưu trữ đối tượng S3 tương thích', icon: HardDrive, key: 's3_storage' as const },
    { name: 'Cơ sở dữ liệu Vector Qdrant', description: 'Lưu trữ vector nhúng tìm kiếm ngữ nghĩa', icon: Database, key: 'qdrant' as const },
    { name: 'Worker xử lý ngầm Celery', description: 'Hàng đợi và tác vụ chạy ngầm', icon: Activity, key: 'celery' as const },
  ]

  const overall = !health
    ? 'Đang kiểm tra...'
    : health.status === 'healthy'
      ? 'Tất cả hệ thống hoạt động tốt'
      : 'Một số dịch vụ gặp sự cố'

  return (
    <div className="space-y-6 font-body">
      <div className="flex flex-col gap-1">
        <h1 className="text-fluid-2xl font-bold text-foreground">Cài Đặt Quản Trị</h1>
        <p className="text-muted-foreground text-sm">Cấu hình nền tảng và giám sát hạ tầng.</p>
      </div>

      <Card className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Key className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-display text-base font-semibold text-foreground">Cấu hình Gemini</h2>
            <p className="text-xs text-muted-foreground">Quản lý API key và model tập trung trong Admin Key Vault.</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => router.push('/app/admin/ai-keys')}>
          <Bot className="mr-1.5 h-3.5 w-3.5" />
          Mở cấu hình Gemini
        </Button>
      </Card>

      {/* System Health */}
      <Card>
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            <h2 className="font-display text-base font-semibold text-foreground">Trạng Thái Hệ Thống</h2>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              variant={!health ? 'default' : health.status === 'healthy' ? 'success' : 'error'}
              label={overall}
              dot
            />
            <Button variant="outline" size="sm" onClick={fetchHealth} loading={loading}>
              Làm mới
            </Button>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-3 p-4 sm:p-5 md:grid-cols-3">
          {services.map((svc) => {
            const status = !health ? 'checking' : (health.services[svc.key] ?? 'offline')
            const statusLabel =
              status === 'healthy'
                ? 'Hoạt động tốt'
                : status === 'checking'
                  ? 'Đang kiểm tra'
                  : status === 'unhealthy'
                    ? 'Gặp sự cố'
                    : 'Ngoại tuyến'
            return (
              <div key={svc.key} className="flex items-center gap-3 p-3 rounded-lg border border-border">
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    status === 'healthy' ? 'bg-success/10' : 'bg-destructive/10'
                  }`}
                >
                  <svc.icon className={`h-5 w-5 ${status === 'healthy' ? 'text-success' : 'text-destructive'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{svc.name}</p>
                  <p className="text-xs text-muted-foreground">{svc.description}</p>
                </div>
                <span
                  className={`text-xs font-semibold ${
                    status === 'healthy'
                      ? 'text-success'
                      : status === 'unhealthy'
                      ? 'text-destructive'
                      : 'text-muted-foreground'
                  }`}
                >
                  {statusLabel}
                </span>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Platform Info */}
      <Card>
        <div className="px-5 py-4 border-b border-border">
          <h2 className="font-display text-base font-semibold text-foreground">Thông Tin Nền Tảng</h2>
        </div>
        <div className="p-5 space-y-3">
          {[
            { label: 'Nền tảng', value: 'MULTIMODAL AI LEARNING HUB' },
            { label: 'Phiên bản', value: '1.0.0' },
            { label: 'Giao diện (Frontend)', value: 'Next.js 16 (App Router) + React 19 + Tailwind CSS' },
            { label: 'Máy chủ (Backend)', value: 'FastAPI + SQLAlchemy + PostgreSQL' },
            { label: 'Động cơ AI (AI Engine)', value: 'LangGraph + Gemini (model do Admin quản lý)' },
          ].map((item) => (
            <div key={item.label} className="flex justify-between text-sm">
              <span className="text-muted-foreground">{item.label}</span>
              <span className="font-medium text-foreground">{item.value}</span>
            </div>
          ))}
        </div>
      </Card>

    </div>
  )
}
