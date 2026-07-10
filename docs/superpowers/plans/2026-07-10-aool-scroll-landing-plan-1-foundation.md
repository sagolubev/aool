# АУЛ Scroll Landing — Plan 1: Foundation + Scroll Engine + Sora Spike

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Стоящий на ногах Next.js-лендинг АУЛ с рабочим scroll-scrub hero на плейсхолдер-ассетах, SSR-контентом и постер-fallback; плюс валидация Sora-2 на одной сцене.

**Architecture:** App Router Next.js (TS). Клиентский компонент `ScrollWorld` портирует `scroll-world/references/scrub-engine.js`: скролл → progress → time/frame видео, lazy-load, seam crossfade, с абстрагированным источником кадра (video-scrub / image-sequence / poster). Контент-секции — SSR. Sora-2 спайк живёт в `spike/` и в CI не участвует.

**Tech Stack:** Next.js 15 (App Router), TypeScript, Vitest (unit), Playwright (E2E), zod (валидация конфига), Azure AI Foundry (Sora-2, только в спайке), ffmpeg.

Спека: `docs/superpowers/specs/2026-07-10-aool-scroll-landing-design.md`

---

## File Structure

- `package.json`, `next.config.mjs`, `tsconfig.json`, `vitest.config.ts`, `playwright.config.ts` — каркас.
- `app/layout.tsx` — метаданные/OG/шрифты.
- `app/page.tsx` — сборка hero + секций.
- `components/ScrollWorld/scrub.ts` — чистая логика progress→frame (тестируемая без DOM).
- `components/ScrollWorld/scenes.ts` — конфиг 6 сцен + zod-схема.
- `components/ScrollWorld/ScrollWorld.tsx` — клиентский компонент, монтирует движок.
- `components/ScrollWorld/useScrubEngine.ts` — хук: подписка на scroll, rAF, выбор источника.
- `components/sections/*` — Houses, Amenities, WhyAul, Manifesto, Cta, Footer (SSR).
- `lib/media.ts` — детект capability (reduced-motion, сеть, canPlay webm).
- `spike/sora-spike.ts` + `spike/README.md` — генерация 1 сцены Sora-2.
- `tests/` — unit + e2e.
- `public/scroll/placeholder/` — плейсхолдер still/clip/frames для разработки.

---

## Task 1: Scaffold Next.js + тулинг

**Files:**
- Create: `package.json`, `next.config.mjs`, `tsconfig.json`, `.gitignore`, `app/layout.tsx`, `app/page.tsx`

- [ ] **Step 1: Инициализировать проект**

Run:
```bash
cd /Users/fnt/work/sigius/myinfra/aool
npx create-next-app@latest . --ts --app --no-tailwind --no-src-dir --eslint --import-alias "@/*" --use-npm --no-turbopack
```
Expected: создан каркас, `app/page.tsx` существует, `npm run dev` поднимается.

- [ ] **Step 2: Инициализировать git и первый коммит**

Run:
```bash
git init && git add -A && git commit -m "chore: scaffold next.js app"
```
Expected: коммит создан (репозитория раньше не было).

- [ ] **Step 3: Проверить сборку**

Run: `npm run build`
Expected: `Compiled successfully`.

- [ ] **Step 4: Коммит**

```bash
git add -A && git commit -m "chore: verify baseline build" --allow-empty
```

---

## Task 2: Чистая логика scrub (progress → frame/time)

Ядро движка — детерминированная функция маппинга. Тестируем без браузера.

**Files:**
- Create: `components/ScrollWorld/scrub.ts`
- Test: `tests/scrub.test.ts`
- Create/Modify: `vitest.config.ts`, `package.json` (scripts)

- [ ] **Step 1: Установить Vitest**

Run: `npm i -D vitest`
Then add to `package.json` scripts: `"test": "vitest run"`, `"test:watch": "vitest"`.
Create `vitest.config.ts`:
```ts
import { defineConfig } from 'vitest/config'
export default defineConfig({ test: { environment: 'node', include: ['tests/**/*.test.ts'] } })
```

- [ ] **Step 2: Написать падающий тест**

`tests/scrub.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { globalProgressToScene, sceneTimeForProgress } from '@/components/ScrollWorld/scrub'

const scenes = [{ durationSec: 2 }, { durationSec: 3 }, { durationSec: 2 }]

describe('globalProgressToScene', () => {
  it('maps start to first scene at t=0', () => {
    expect(globalProgressToScene(0, scenes)).toEqual({ index: 0, sceneProgress: 0 })
  })
  it('maps end to last scene at t=1', () => {
    expect(globalProgressToScene(1, scenes)).toEqual({ index: 2, sceneProgress: 1 })
  })
  it('splits by scene duration, not evenly', () => {
    // total 7s; 2s boundary at 2/7 ≈ 0.2857
    const r = globalProgressToScene(2 / 7, scenes)
    expect(r.index).toBe(1)
    expect(r.sceneProgress).toBeCloseTo(0, 5)
  })
  it('clamps out-of-range progress', () => {
    expect(globalProgressToScene(-0.5, scenes).index).toBe(0)
    expect(globalProgressToScene(1.5, scenes).index).toBe(2)
  })
})

describe('sceneTimeForProgress', () => {
  it('returns video currentTime for a scene', () => {
    expect(sceneTimeForProgress(0.5, 4)).toBeCloseTo(2, 5)
  })
})
```

- [ ] **Step 3: Запустить — должно упасть**

Run: `npm test`
Expected: FAIL, `scrub.ts` не найден.

- [ ] **Step 4: Реализовать минимально**

`components/ScrollWorld/scrub.ts`:
```ts
export interface SceneTiming { durationSec: number }

export function globalProgressToScene(p: number, scenes: SceneTiming[]) {
  const clamped = Math.min(1, Math.max(0, p))
  const total = scenes.reduce((s, x) => s + x.durationSec, 0)
  let acc = 0
  const target = clamped * total
  for (let i = 0; i < scenes.length; i++) {
    const start = acc
    const end = acc + scenes[i].durationSec
    if (target <= end || i === scenes.length - 1) {
      const span = scenes[i].durationSec || 1
      const sceneProgress = Math.min(1, Math.max(0, (target - start) / span))
      return { index: i, sceneProgress: clamped >= 1 ? 1 : sceneProgress }
    }
    acc = end
  }
  return { index: scenes.length - 1, sceneProgress: 1 }
}

export function sceneTimeForProgress(sceneProgress: number, durationSec: number) {
  return Math.min(1, Math.max(0, sceneProgress)) * durationSec
}
```

- [ ] **Step 5: Запустить — должно пройти**

Run: `npm test`
Expected: PASS (5 тестов).

- [ ] **Step 6: Коммит**

```bash
git add components/ScrollWorld/scrub.ts tests/scrub.test.ts vitest.config.ts package.json
git commit -m "feat: scroll scrub progress-to-frame mapping"
```

---

## Task 3: Конфиг сцен + zod-валидация

**Files:**
- Create: `components/ScrollWorld/scenes.ts`
- Test: `tests/scenes.test.ts`

- [ ] **Step 1: Установить zod**

Run: `npm i zod`

- [ ] **Step 2: Падающий тест**

`tests/scenes.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { SceneSchema, scenes } from '@/components/ScrollWorld/scenes'

describe('scenes config', () => {
  it('has exactly 6 scenes', () => {
    expect(scenes.length).toBe(6)
  })
  it('every scene passes the schema', () => {
    for (const s of scenes) expect(() => SceneSchema.parse(s)).not.toThrow()
  })
  it('scene ids are unique and ordered 1..6', () => {
    expect(scenes.map(s => s.order)).toEqual([1, 2, 3, 4, 5, 6])
  })
  it('rejects a scene missing a still', () => {
    expect(() => SceneSchema.parse({ id: 'x', order: 1, title: 't', durationSec: 2, clip: '/a.webm' }))
      .toThrow()
  })
})
```

- [ ] **Step 3: Запустить — упадёт**

Run: `npm test tests/scenes.test.ts`
Expected: FAIL, `scenes.ts` не найден.

- [ ] **Step 4: Реализовать**

`components/ScrollWorld/scenes.ts`:
```ts
import { z } from 'zod'

export const SceneSchema = z.object({
  id: z.string().min(1),
  order: z.number().int().positive(),
  title: z.string().min(1),
  subtitle: z.string().optional(),
  durationSec: z.number().positive(),
  still: z.string().min(1),
  clip: z.string().min(1),
  connector: z.string().optional(),
})
export type Scene = z.infer<typeof SceneSchema>

const P = '/scroll/placeholder'
export const scenes: Scene[] = [
  { id: 'forest', order: 1, title: 'Лес', subtitle: '25 км от Уфы. Тишина.', durationSec: 2, still: `${P}/1.jpg`, clip: `${P}/1.webm`, connector: `${P}/c1.webm` },
  { id: 'gate', order: 2, title: 'Въезд', subtitle: 'Стела «Родная земля»', durationSec: 2, still: `${P}/2.jpg`, clip: `${P}/2.webm`, connector: `${P}/c2.webm` },
  { id: 'alley', order: 3, title: 'Центральная аллея', subtitle: '25 га благоустройства', durationSec: 2, still: `${P}/3.jpg`, clip: `${P}/3.webm`, connector: `${P}/c3.webm` },
  { id: 'house', order: 4, title: 'Дом', subtitle: 'Земля · Огонь · Воздух · Вода', durationSec: 2, still: `${P}/4.jpg`, clip: `${P}/4.webm`, connector: `${P}/c4.webm` },
  { id: 'interior', order: 5, title: 'Внутри', subtitle: 'Потолки до 4,7 м', durationSec: 2, still: `${P}/5.jpg`, clip: `${P}/5.webm`, connector: `${P}/c5.webm` },
  { id: 'garden', order: 6, title: 'Сад', subtitle: 'Приватность и BBQ', durationSec: 2, still: `${P}/6.jpg`, clip: `${P}/6.webm` },
]
```

- [ ] **Step 5: Запустить — пройдёт**

Run: `npm test tests/scenes.test.ts`
Expected: PASS.

- [ ] **Step 6: Коммит**

```bash
git add components/ScrollWorld/scenes.ts tests/scenes.test.ts package.json
git commit -m "feat: scene config with zod validation"
```

---

## Task 4: Детект возможностей медиа

**Files:**
- Create: `lib/media.ts`
- Test: `tests/media.test.ts`

- [ ] **Step 1: Падающий тест**

`tests/media.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { chooseRenderMode } from '@/lib/media'

describe('chooseRenderMode', () => {
  it('poster when reduced motion', () => {
    expect(chooseRenderMode({ reducedMotion: true, canPlayWebm: true, saveData: false })).toBe('poster')
  })
  it('image-sequence when webm unsupported', () => {
    expect(chooseRenderMode({ reducedMotion: false, canPlayWebm: false, saveData: false })).toBe('image-sequence')
  })
  it('poster when save-data', () => {
    expect(chooseRenderMode({ reducedMotion: false, canPlayWebm: true, saveData: true })).toBe('poster')
  })
  it('video-scrub in the good case', () => {
    expect(chooseRenderMode({ reducedMotion: false, canPlayWebm: true, saveData: false })).toBe('video-scrub')
  })
})
```

- [ ] **Step 2: Запустить — упадёт**

Run: `npm test tests/media.test.ts`
Expected: FAIL.

- [ ] **Step 3: Реализовать**

`lib/media.ts`:
```ts
export type RenderMode = 'video-scrub' | 'image-sequence' | 'poster'

export interface MediaCaps {
  reducedMotion: boolean
  canPlayWebm: boolean
  saveData: boolean
}

export function chooseRenderMode(c: MediaCaps): RenderMode {
  if (c.reducedMotion || c.saveData) return 'poster'
  if (!c.canPlayWebm) return 'image-sequence'
  return 'video-scrub'
}

export function detectCaps(): MediaCaps {
  if (typeof window === 'undefined') return { reducedMotion: true, canPlayWebm: false, saveData: false }
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const v = document.createElement('video')
  const canPlayWebm = !!v.canPlayType('video/webm; codecs="vp9"')
  const conn = (navigator as any).connection
  const saveData = !!(conn && conn.saveData)
  return { reducedMotion, canPlayWebm, saveData }
}
```

- [ ] **Step 4: Запустить — пройдёт**

Run: `npm test tests/media.test.ts`
Expected: PASS.

- [ ] **Step 5: Коммит**

```bash
git add lib/media.ts tests/media.test.ts
git commit -m "feat: media capability detection and render-mode selection"
```

---

## Task 5: Плейсхолдер-ассеты для разработки

Позволяют собрать hero до появления Sora-ассетов.

**Files:**
- Create: `public/scroll/placeholder/*` (сгенерированные), `scripts/gen-placeholders.sh`

- [ ] **Step 1: Скрипт генерации через ffmpeg**

`scripts/gen-placeholders.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
out=public/scroll/placeholder
mkdir -p "$out"
colors=(2d4a3e 3a5a4a 4a6a55 5a7a60 6a8a6b 7a9a76)
for i in $(seq 1 6); do
  c=${colors[$((i-1))]}
  ffmpeg -y -f lavfi -i "color=c=0x${c}:s=1280x720:d=2" \
    -vf "drawtext=text='SCENE ${i}':fontcolor=white:fontsize=72:x=(w-tw)/2:y=(h-th)/2" \
    -c:v libvpx-vp9 -b:v 1M "$out/${i}.webm"
  ffmpeg -y -i "$out/${i}.webm" -frames:v 1 "$out/${i}.jpg"
  if [ "$i" -lt 6 ]; then
    ffmpeg -y -f lavfi -i "color=c=0x${c}:s=1280x720:d=1" -c:v libvpx-vp9 -b:v 1M "$out/c${i}.webm"
  fi
done
echo "placeholders ready in $out"
```

- [ ] **Step 2: Запустить**

Run: `bash scripts/gen-placeholders.sh`
Expected: `1.webm..6.webm`, `1.jpg..6.jpg`, `c1..c5.webm` в `public/scroll/placeholder/`.

- [ ] **Step 3: gitignore тяжёлых webm, но оставить jpg-постеры**

Add to `.gitignore`:
```
public/scroll/placeholder/*.webm
public/scroll/**/*.mp4
```
(Постеры `*.jpg` коммитим — нужны для fallback-тестов.)

- [ ] **Step 4: Коммит**

```bash
git add scripts/gen-placeholders.sh .gitignore public/scroll/placeholder/*.jpg
git commit -m "chore: placeholder asset generator for dev"
```

---

## Task 6: ScrollWorld компонент + хук

**Files:**
- Create: `components/ScrollWorld/useScrubEngine.ts`, `components/ScrollWorld/ScrollWorld.tsx`, `components/ScrollWorld/ScrollWorld.module.css`

- [ ] **Step 1: Хук движка (video-scrub через rAF)**

`components/ScrollWorld/useScrubEngine.ts`:
```ts
'use client'
import { useEffect, useRef, useState } from 'react'
import { globalProgressToScene, sceneTimeForProgress } from './scrub'
import type { Scene } from './scenes'
import { detectCaps, chooseRenderMode, type RenderMode } from '@/lib/media'

export function useScrubEngine(scenes: Scene[], sectionRef: React.RefObject<HTMLElement>) {
  const [mode, setMode] = useState<RenderMode>('poster')
  const [active, setActive] = useState(0)
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([])
  const raf = useRef<number>(0)

  useEffect(() => { setMode(chooseRenderMode(detectCaps())) }, [])

  useEffect(() => {
    if (mode !== 'video-scrub') return
    const timings = scenes.map(s => ({ durationSec: s.durationSec }))
    const onScroll = () => {
      cancelAnimationFrame(raf.current)
      raf.current = requestAnimationFrame(() => {
        const el = sectionRef.current
        if (!el) return
        const rect = el.getBoundingClientRect()
        const total = el.offsetHeight - window.innerHeight
        const p = total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 0
        const { index, sceneProgress } = globalProgressToScene(p, timings)
        setActive(index)
        const v = videoRefs.current[index]
        if (v && v.duration) v.currentTime = sceneTimeForProgress(sceneProgress, v.duration)
      })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => { window.removeEventListener('scroll', onScroll); cancelAnimationFrame(raf.current) }
  }, [mode, scenes, sectionRef])

  return { mode, active, videoRefs }
}
```

- [ ] **Step 2: Компонент**

`components/ScrollWorld/ScrollWorld.tsx`:
```tsx
'use client'
import { useRef } from 'react'
import { scenes } from './scenes'
import { useScrubEngine } from './useScrubEngine'
import styles from './ScrollWorld.module.css'

export function ScrollWorld() {
  const sectionRef = useRef<HTMLElement>(null)
  const { mode, active, videoRefs } = useScrubEngine(scenes, sectionRef)

  return (
    <section ref={sectionRef} className={styles.world} style={{ height: `${scenes.length * 100}vh` }} data-mode={mode}>
      <div className={styles.sticky}>
        {mode === 'poster' ? (
          <img src={scenes[0].still} alt={scenes[0].title} className={styles.layer} />
        ) : (
          scenes.map((s, i) => (
            <video
              key={s.id}
              ref={el => { videoRefs.current[i] = el }}
              src={s.clip}
              poster={s.still}
              muted playsInline preload={i === 0 ? 'auto' : 'none'}
              className={styles.layer}
              style={{ opacity: i === active ? 1 : 0 }}
            />
          ))
        )}
        <div className={styles.caption} key={active}>
          <h2>{scenes[active]?.title}</h2>
          {scenes[active]?.subtitle && <p>{scenes[active].subtitle}</p>}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 3: Стили (sticky + crossfade)**

`components/ScrollWorld/ScrollWorld.module.css`:
```css
.world { position: relative; }
.sticky { position: sticky; top: 0; height: 100vh; overflow: hidden; }
.layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transition: opacity .35s ease; }
.caption { position: absolute; left: 6vw; bottom: 12vh; color: #fff; text-shadow: 0 2px 20px rgba(0,0,0,.5); }
.caption h2 { font-size: clamp(2rem, 6vw, 5rem); margin: 0; }
.caption p { font-size: clamp(1rem, 2vw, 1.5rem); opacity: .85; }
```

- [ ] **Step 4: Проверить в dev вручную**

Run: `npm run dev` и открыть `http://localhost:3000` (после Task 7 hero будет на странице).
Expected: сборка без ошибок TS (`npm run build`).

- [ ] **Step 5: Коммит**

```bash
git add components/ScrollWorld/
git commit -m "feat: scroll-world hero component with video-scrub and poster fallback"
```

---

## Task 7: Контент-секции (SSR) + сборка страницы

**Files:**
- Create: `components/sections/Houses.tsx`, `Amenities.tsx`, `WhyAul.tsx`, `Manifesto.tsx`, `Cta.tsx`, `Footer.tsx`
- Modify: `app/page.tsx`, `app/layout.tsx`

- [ ] **Step 1: Houses (данные из aool.space)**

`components/sections/Houses.tsx`:
```tsx
const houses = [
  { name: 'Земля', area: 226, floors: 1 },
  { name: 'Огонь', area: 321, floors: 2 },
  { name: 'Воздух', area: 428, floors: 1 },
  { name: 'Вода', area: 362, floors: 2 },
]
export function Houses() {
  return (
    <section id="houses" style={{ padding: '8vh 6vw' }}>
      <h2>Дома</h2>
      <p>Стоимость от 38 млн ₽. 4 типа в едином архитектурном стиле.</p>
      <ul style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 24, listStyle: 'none', padding: 0 }}>
        {houses.map(h => (
          <li key={h.name} style={{ border: '1px solid #ddd', borderRadius: 12, padding: 20 }}>
            <h3>Дом «{h.name}»</h3>
            <p>{h.area} м² · {h.floors} эт.</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
```

- [ ] **Step 2: Остальные секции (минимальный SSR-контент)**

`components/sections/Amenities.tsx`:
```tsx
export function Amenities() {
  return (
    <section id="amenities" style={{ padding: '8vh 6vw' }}>
      <h2>Благоустройство</h2>
      <p>103 дома на 25 гектарах: лобби, ресторан, бассейн, банный комплекс, детский сад, амфитеатр, теннисный корт, скейт-парк.</p>
    </section>
  )
}
```
`components/sections/WhyAul.tsx`:
```tsx
export function WhyAul() {
  const facts = ['Потолки до 4,7 м', 'Остекление фасадов до 30%', 'Террасы в каждом доме', 'Участки 9–27 соток', 'Монолитный каркас', 'Гарантия 3 года']
  return (
    <section id="why" style={{ padding: '8vh 6vw' }}>
      <h2>Почему АУЛ</h2>
      <ul>{facts.map(f => <li key={f}>{f}</li>)}</ul>
    </section>
  )
}
```
`components/sections/Manifesto.tsx`:
```tsx
export function Manifesto() {
  return (
    <section id="manifesto" style={{ padding: '12vh 6vw', background: '#f5f2ec' }}>
      <blockquote style={{ maxWidth: 760, margin: '0 auto', fontSize: '1.4rem', lineHeight: 1.5 }}>
        Черпать силу из древнего, обретать устойчивость в корнях, брать лучшее из
        современного — основные смыслы пространства АУЛ.
      </blockquote>
    </section>
  )
}
```
`components/sections/Cta.tsx`:
```tsx
export function Cta() {
  return (
    <section id="cta" style={{ padding: '12vh 6vw', textAlign: 'center' }}>
      <h2>Выберите свой дом</h2>
      <a href="https://aool.space/doma/" style={{ display: 'inline-block', marginTop: 16, padding: '14px 28px', background: '#2d4a3e', color: '#fff', borderRadius: 8, textDecoration: 'none' }}>Выбрать дом</a>
    </section>
  )
}
```
`components/sections/Footer.tsx`:
```tsx
export function Footer() {
  return (
    <footer style={{ padding: '6vh 6vw', color: '#666' }}>
      <p>Посёлок АУЛ · Уфа, село Акбердино · 25 км от центра города</p>
    </footer>
  )
}
```

- [ ] **Step 3: Сборка страницы**

`app/page.tsx`:
```tsx
import { ScrollWorld } from '@/components/ScrollWorld/ScrollWorld'
import { Houses } from '@/components/sections/Houses'
import { Amenities } from '@/components/sections/Amenities'
import { WhyAul } from '@/components/sections/WhyAul'
import { Manifesto } from '@/components/sections/Manifesto'
import { Cta } from '@/components/sections/Cta'
import { Footer } from '@/components/sections/Footer'

export default function Page() {
  return (
    <main>
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
```

- [ ] **Step 4: Метаданные/SEO**

`app/layout.tsx` — задать `metadata`:
```tsx
export const metadata = {
  title: 'Посёлок АУЛ — премиум-резиденция в 25 км от Уфы',
  description: 'Дома 226–428 м² с участками до 24 соток. Пространство на крепких традициях, с атмосферой безопасности и теплом дома.',
  openGraph: { title: 'Посёлок АУЛ', description: 'Премиум-резиденция под Уфой', type: 'website' },
}
```

- [ ] **Step 5: Проверить сборку**

Run: `npm run build`
Expected: `Compiled successfully`, страница `/` пререндерится.

- [ ] **Step 6: Коммит**

```bash
git add components/sections/ app/page.tsx app/layout.tsx
git commit -m "feat: content sections and landing page assembly"
```

---

## Task 8: E2E — hero-скролл и fallback

**Files:**
- Create: `playwright.config.ts`, `tests/e2e/landing.spec.ts`
- Modify: `package.json` (scripts)

- [ ] **Step 1: Установить Playwright**

Run: `npm i -D @playwright/test && npx playwright install chromium`
Add script: `"e2e": "playwright test"`.

- [ ] **Step 2: Конфиг**

`playwright.config.ts`:
```ts
import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: 'tests/e2e',
  webServer: { command: 'npm run build && npm run start', url: 'http://localhost:3000', reuseExistingServer: !process.env.CI, timeout: 120_000 },
  use: { baseURL: 'http://localhost:3000' },
})
```

- [ ] **Step 3: Тест SSR-контента и fallback**

`tests/e2e/landing.spec.ts`:
```ts
import { test, expect } from '@playwright/test'

test('SSR renders scene captions and content sections', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Лес' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Дома' })).toBeVisible()
  await expect(page.getByText('от 38 млн')).toBeVisible()
})

test('reduced-motion renders poster hero, not scrub video', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await ctx.newPage()
  await page.goto('/')
  await expect(page.locator('section[data-mode="poster"]')).toBeVisible()
  await ctx.close()
})

test('scroll advances hero caption', async ({ page }) => {
  await page.goto('/')
  await page.mouse.wheel(0, 2500)
  await expect(page.getByRole('heading', { name: /Въезд|Центральная аллея/ })).toBeVisible()
})
```

- [ ] **Step 4: Запустить**

Run: `npm run e2e`
Expected: 3 теста PASS. (Плейсхолдер-webm gitignored — сгенерировать перед прогоном: `bash scripts/gen-placeholders.sh`.)

- [ ] **Step 5: Коммит**

```bash
git add playwright.config.ts tests/e2e/ package.json
git commit -m "test: e2e for hero scroll and reduced-motion fallback"
```

---

## Task 9: Sora-2 спайк (gate перед Plan 2)

Изолированный скрипт: генерит 1 сцену + 1 коннектор на Sora-2 через Azure AI Foundry, отдаёт файлы для ручной проверки бесшовности. **Не** часть приложения/CI.

**Files:**
- Create: `spike/sora-spike.ts`, `spike/README.md`, `spike/.env.example`

- [ ] **Step 1: Документировать доступ**

`spike/.env.example`:
```
AZURE_FOUNDRY_ENDPOINT=https://<resource>.services.ai.azure.com
AZURE_FOUNDRY_API_KEY=
SORA_DEPLOYMENT=sora-2
```
`spike/README.md` — как заполнить, как запустить, что проверяем: (1) держит ли Sora стиль/свет между still→clip; (2) бесшовен ли стык clip→connector с crossfade; (3) вес клипа при 1280x720.

- [ ] **Step 2: Скрипт генерации (image-to-video)**

`spike/sora-spike.ts`:
```ts
// Прогон: npx tsx spike/sora-spike.ts
// Требует Azure AI Foundry с деплоем Sora-2. Пишет out/*.mp4.
import { writeFile } from 'node:fs/promises'

const endpoint = process.env.AZURE_FOUNDRY_ENDPOINT!
const key = process.env.AZURE_FOUNDRY_API_KEY!
const deployment = process.env.SORA_DEPLOYMENT || 'sora-2'

async function generate(prompt: string, seconds = 4): Promise<Buffer> {
  const res = await fetch(`${endpoint}/openai/deployments/${deployment}/video/generations?api-version=2025-04-01-preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'api-key': key },
    body: JSON.stringify({ prompt, n_seconds: seconds, size: '1280x720' }),
  })
  if (!res.ok) throw new Error(`Sora ${res.status}: ${await res.text()}`)
  const buf = Buffer.from(await res.arrayBuffer())
  return buf
}

async function main() {
  const scene = await generate('Isometric diorama, cinematic camera slowly diving into a modern forest village at 25km from a city, morning light, calm, photoreal', 4)
  await writeFile('spike/out/scene.mp4', scene)
  console.log('scene.mp4 written — проверь стиль/вес; для connector сгенерируй продолжение с тем же промптом и фикс-сидом')
}
main().catch(e => { console.error(e); process.exit(1) })
```
> Примечание: точный shape запроса (endpoint/params/async-poll) сверить с актуальной докой Azure AI Foundry Sora на момент прогона — API preview меняется. README фиксирует это как обязательный шаг.

- [ ] **Step 3: Прогнать (ручной гейт, вне автотестов)**

Run:
```bash
mkdir -p spike/out
cp spike/.env.example spike/.env   # заполнить ключи
npx tsx spike/sora-spike.ts
```
Expected: `spike/out/scene.mp4`. Открыть, оценить по критериям README. **Решение фиксируется в Plan 2:** video-scrub годится, или переключаемся на image-sequence.

- [ ] **Step 4: Коммит (без ассетов/секретов)**

Add to `.gitignore`: `spike/out/`, `spike/.env`.
```bash
git add spike/sora-spike.ts spike/README.md spike/.env.example .gitignore
git commit -m "chore: sora-2 azure foundry spike harness"
```

---

## Definition of Done (Plan 1)

- `npm run build` зелёный; `npm test` (unit) и `npm run e2e` проходят.
- Лендинг открывается: hero скроллится на плейсхолдерах, reduced-motion → постер, контент-секции в SSR-разметке.
- Спайк Sora-2 прогнан, решение (video-scrub / image-sequence) записано во входные данные Plan 2.

## Что дальше

- **Plan 2:** asset pipeline — генерация 6 сцен + коннекторов выбранным подходом, замена плейсхолдеров в `scenes.ts`, ffmpeg-кодирование webm+mp4, оптимизация LCP.
- **Plan 3:** финальный контент/копирайт, реальные фото домов, Dockerfile + ArgoCD Application в `infra/`, деплой в AKS.
