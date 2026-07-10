import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Посёлок АУЛ — премиум-резиденция в 25 км от Уфы',
  description:
    'Дома 226–428 м² с участками до 24 соток. Пространство на крепких традициях, с атмосферой безопасности и теплом дома. Село Акбердино.',
  openGraph: {
    title: 'Посёлок АУЛ',
    description: 'Премиум-резиденция под Уфой — 103 дома на 25 гектарах.',
    type: 'website',
    locale: 'ru_RU',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  )
}
