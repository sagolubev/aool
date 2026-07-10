import { ScrollWorld } from '@/components/ScrollWorld/ScrollWorld'
import { Houses } from '@/components/sections/Houses'
import { Amenities } from '@/components/sections/Amenities'
import { WhyAul } from '@/components/sections/WhyAul'
import { Manifesto } from '@/components/sections/Manifesto'
import { Cta } from '@/components/sections/Cta'
import { Footer } from '@/components/sections/Footer'

export default function Page() {
  return (
    <main id="top">
      <ScrollWorld />
      {/* Контент секций — в DOM для SEO/доступности; визуально ведёт scroll-world. */}
      <div className="seo-only">
        <h1>Посёлок АУЛ — премиум-резиденция в 25 км от Уфы</h1>
        <Houses />
        <Amenities />
        <WhyAul />
        <Manifesto />
        <Cta />
        <Footer />
      </div>
    </main>
  )
}
