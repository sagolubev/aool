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
      <Houses />
      <Amenities />
      <WhyAul />
      <Manifesto />
      <Cta />
      <Footer />
    </main>
  )
}
