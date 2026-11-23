import { useNavigate } from "react-router-dom"
import { Compass, Home } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center p-4">
      <Card className="w-full max-w-md text-center border-border/80 shadow-md">
        <CardHeader className="pb-2">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Compass className="h-8 w-8" />
          </div>
          <CardTitle className="text-3xl font-extrabold tracking-tight">404</CardTitle>
          <CardDescription className="text-base font-medium text-foreground mt-1">
            Không tìm thấy trang
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Đường dẫn bạn yêu cầu không tồn tại hoặc đã được di chuyển trong hệ thống EduVision BI.
        </CardContent>
        <CardFooter className="justify-center border-t border-border/50 pt-4">
          <Button
            onClick={() => navigate("/tong-quan")}
            className="gap-2 cursor-pointer"
          >
            <Home className="h-4 w-4" />
            <span>Quay về trang Tổng quan</span>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
