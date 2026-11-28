'use client'

interface PlaceholderPageProps {
  title: string
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <div className="flex h-[60vh] items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-foreground">{title}</h1>
        <p className="text-muted-foreground mt-2">Tính năng này đang được phát triển.</p>
      </div>
    </div>
  )
}
