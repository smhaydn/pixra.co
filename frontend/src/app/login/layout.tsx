import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Pixra - Giriş Yap',
  description: 'Pixra AI E-Ticaret SEO platformuna giriş yapın',
}

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
