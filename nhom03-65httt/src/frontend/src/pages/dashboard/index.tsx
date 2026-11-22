import React, { useState, useRef } from "react"
import {
  Maximize2,
  Minimize2,
  RefreshCw,
  ExternalLink,
  AlertTriangle,
  Info,
  LineChart,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"

export default function DashboardPage() {
  const supersetUrl = import.meta.env.VITE_SUPERSET_DASHBOARD_URL
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  const toggleFullscreen = async () => {
    if (!containerRef.current) return

    if (!document.fullscreenElement) {
      try {
        await containerRef.current.requestFullscreen()
        setIsFullscreen(true)
      } catch (err) {
        console.error("Lỗi khi mở toàn màn hình:", err)
      }
    } else {
      try {
        await document.exitFullscreen()
        setIsFullscreen(false)
      } catch (err) {
        console.error("Lỗi khi thoát toàn màn hình:", err)
      }
    }
  }

  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener("fullscreenchange", handleFullscreenChange)
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange)
  }, [])

  const reloadIframe = () => {
    if (iframeRef.current) {
      setIsLoading(true)
      setHasError(false)
      iframeRef.current.src = iframeRef.current.src
    }
  }

  return (
    <div className="space-y-4">
      {/* Page Header responsive */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight">Dashboard Superset</h1>
            <Badge variant="outline" className="text-[11px] py-0 h-5">
              Apache Superset Embedded
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Trực quan hóa chỉ số BHI, phân tích cảm xúc và so sánh đa chiều giữa 9 nền tảng E-learning.
          </p>
        </div>

        {supersetUrl && (
          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={reloadIframe}
              className="gap-1.5 text-xs h-8 cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span>Làm mới</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={toggleFullscreen}
              className="gap-1.5 text-xs h-8 cursor-pointer"
            >
              {isFullscreen ? (
                <>
                  <Minimize2 className="h-3.5 w-3.5" />
                  <span>Thu nhỏ</span>
                </>
              ) : (
                <>
                  <Maximize2 className="h-3.5 w-3.5" />
                  <span>Toàn màn hình</span>
                </>
              )}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              asChild
              className="gap-1.5 text-xs h-8"
            >
              <a href={supersetUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3.5 w-3.5" />
                <span>Mở tab mới</span>
              </a>
            </Button>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {!supersetUrl ? (
        /* Thẻ giữ chỗ khi chưa cấu hình Superset */
        <Card className="border-border/80 shadow-sm">
          <CardHeader className="text-center pb-2 px-4 sm:px-6">
            <div className="mx-auto mb-2.5 flex h-12 w-12 sm:h-14 sm:w-14 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <LineChart className="h-6 w-6 sm:h-7 sm:w-7" />
            </div>
            <CardTitle className="text-lg sm:text-xl font-bold">Chưa cấu hình Superset</CardTitle>
            <CardDescription className="text-xs sm:text-sm max-w-md mx-auto">
              Biến môi trường <code>VITE_SUPERSET_DASHBOARD_URL</code> hiện đang để trống hoặc chưa được cấu hình.
            </CardDescription>
          </CardHeader>

          <CardContent className="max-w-xl mx-auto space-y-3.5 px-4 sm:px-6 pt-1">
            <div className="rounded-lg border border-border bg-muted/40 p-3 sm:p-4 text-xs space-y-2">
              <div className="flex items-center gap-1.5 font-semibold text-foreground">
                <Info className="h-4 w-4 text-primary shrink-0" />
                <span>Hướng dẫn cấu hình kết nối Superset:</span>
              </div>
              <ol className="list-decimal list-inside space-y-1.5 text-muted-foreground pl-0.5 leading-relaxed">
                <li>
                  Tạo tệp <code>.env</code> tại thư mục <code>nhom03-65httt/src/frontend/</code> (theo mẫu <code>.env.example</code>).
                </li>
                <li>
                  Gán URL dashboard nhúng của Superset:
                  <div className="my-1 rounded bg-background p-2 font-mono text-[11px] text-foreground border border-border overflow-x-auto">
                    VITE_SUPERSET_DASHBOARD_URL=http://localhost:8088/superset/dashboard/.../?standalone=true
                  </div>
                </li>
                <li>
                  Khởi động lại máy chủ dev (<code>npm run dev</code>).
                </li>
              </ol>
            </div>

            <div className="flex items-center justify-center gap-2 text-[11px] sm:text-xs text-muted-foreground text-center">
              <span>Đề cương mục 5 & 11: 6 Dashboard so sánh 9 nền tảng E-learning</span>
            </div>
          </CardContent>
        </Card>
      ) : (
        /* Khung Iframe Responsive */
        <div
          ref={containerRef}
          className={`relative w-full overflow-hidden rounded-xl border border-border bg-card shadow-sm transition-all ${
            isFullscreen
              ? "fixed inset-0 z-50 rounded-none border-0 h-screen w-screen"
              : "min-h-[420px] sm:min-h-[550px] md:min-h-[620px] aspect-video"
          }`}
        >
          {/* Skeleton Loading State */}
          {isLoading && !hasError && (
            <div className="absolute inset-0 flex flex-col gap-3 p-4 sm:p-6 bg-card z-10">
              <div className="flex items-center justify-between">
                <Skeleton className="h-7 w-48 sm:w-64" />
                <Skeleton className="h-7 w-24 sm:w-32" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Skeleton className="h-20 sm:h-24 w-full" />
                <Skeleton className="h-20 sm:h-24 w-full" />
                <Skeleton className="h-20 sm:h-24 w-full" />
              </div>
              <Skeleton className="flex-1 w-full min-h-[300px]" />
            </div>
          )}

          {/* Error Message */}
          {hasError && (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-4 sm:p-6 bg-card z-10 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-2.5">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-base sm:text-lg text-foreground">Không thể tải Dashboard Superset</h3>
              <p className="text-xs sm:text-sm text-muted-foreground max-w-md mt-1 leading-relaxed">
                Không thể kết nối đến máy chủ Superset tại URL đã cấu hình. Vui lòng kiểm tra Docker Superset đã chạy và hỗ trợ nhúng iframe.
              </p>
              <div className="flex flex-wrap gap-2 mt-3.5 justify-center">
                <Button variant="outline" size="sm" onClick={reloadIframe} className="cursor-pointer text-xs">
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                  Thử lại
                </Button>
                <Button variant="secondary" size="sm" asChild className="text-xs">
                  <a href={supersetUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
                    Mở trực tiếp
                  </a>
                </Button>
              </div>
            </div>
          )}

          {/* Iframe */}
          <iframe
            ref={iframeRef}
            src={supersetUrl}
            title="EduVision BI - Apache Superset Dashboard"
            className="w-full h-full min-h-[420px] sm:min-h-[550px] md:min-h-[620px] border-0"
            allow="fullscreen"
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setIsLoading(false)
              setHasError(true)
            }}
          />
        </div>
      )}
    </div>
  )
}
