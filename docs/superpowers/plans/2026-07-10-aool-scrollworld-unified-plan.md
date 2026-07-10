# АУЛ Scroll-World Landing — Unified Execution Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task. Steps use `- [ ]` checkboxes.

**Goal:** Лендинг посёлка АУЛ со scroll-scrub «пролётом сквозь мир» (scroll-world engine), где визуал сгенерён на **Sora-2 (Azure)**, смонтирован в **Next.js**, сценарий «путь в дом» (6 сцен), плюс SSR-секции для SEO.

**Architecture:** scroll-world **Architecture A** (непрерывный forward-take: каждая leg сшивается со следующей по её реальному последнему кадру, коннекторов нет, seam = малый crossfade движка). Генератор — Sora-2 вместо Higgsfield (валидировано спайком, см. `spike/README.md`). Движок `references/scrub-engine.js` — vanilla, монтируется в клиентский Next.js-компонент.

**Tech Stack:** Next.js (App Router, TS), scroll-world `scrub-engine.js`, Sora-2 + gpt-image-2 (Azure, `spike/sora_lib.py`), ffmpeg, Playwright (QA seams).

Спека: `docs/superpowers/specs/2026-07-10-aool-scroll-landing-design.md` · Спайк: `spike/`

* * *
## Chaining-стратегия (важно — реальные ассеты vs CG)
Чистый Architecture A уводит камеру от реального рендера дома. Для недвижимости дом обязан быть узнаваемым, поэтому **гибрид, честно размеченный по seam'ам**:

- **Стрелка 1 (природа/подъезд), сцены 1→2→3:** forward-chain — leg N seed = реальный последний кадр leg N-1. Sora сама держит связный мир (t2v старт на сцене 1).
  
- **Якорь (дом), сцены 4→5→6:** i2v из **реального рендера Дома «Вода»** с сайта → сквозь стекло → интерьер (gpt-image-2 стилл для контроля) → терраса/сад. Внутри якоря — тот же forward-chain по last-frame (спайк это доказал: 12с 4→5 бесшовно).
  
- **Стык 3↔4 (аллея→дом):** контент-переход природа→дом закрываем **crossfade движка** (~0.12vh) + смена копирайта. Небольшой скачок допустим и осмыслен (прибытие к дому).
  

Итог: 6 leg-клипов, коннекторов нет, 1 «смысловой» seam на стыке стрелки и якоря.

* * *
## Сцены (6, «путь в дом»)
| #   | id  | Тип генерации | Seed/anchor |
| --- | --- | --- | --- |
| 1   | forest | t2v establishing | — (art-direction lock) |
| 2   | gate | i2v forward | last frame сцены 1 |
| 3   | alley | i2v forward | last frame сцены 2 |
| 4   | house | i2v (реальный рендер Вода) | `ref/voda_1280.png` |
| 5   | interior | i2v | last frame сцены 4 (сквозь стекло) |
| 6   | garden | i2v | last frame сцены 5 |

Копирайт секций (eyebrow/title/body/tags) — из контента aool.space: Родство/Среда/Ценности, факты (25 км, 25 га, 103 дома, потолки 4.7, от 38 млн).

* * *
## File Structure
```
spike/                      # уже есть: sora_lib.py, sora_i2v.py, README
scripts/
  gen_scenes.py             # генерация 6 leg-клипов (Architecture A chain) на Sora-2
  encode.sh                 # Step 6 энкод: native-res, -g8, unsharp, faststart, +webm
app/
  layout.tsx                # metadata/OG/SEO
  page.tsx                  # <ScrollWorld/> + SSR-секции
components/
  ScrollWorld/
    ScrollWorld.tsx         # 'use client' — монтирует scrub-engine.js через useEffect
    scrub-engine.js         # копия из .claude/skills/scroll-world/references/
    scenes.ts               # config: sections[], connectors:[], copy
  sections/                 # Houses, Amenities, WhyAul, Manifesto, Cta, Footer (SSR)
public/scroll/              # <id>.mp4 (+ .webm), <id>.webp постеры  (gitignored mp4)
tests/e2e/                  # Playwright: seam-QA + SSR + reduced-motion
```

* * *
## Task 1: Генерация 6 leg-клипов (Sora-2, Architecture A)
**Files:** Create `scripts/gen_scenes.py`

- [ ] 
  
  **Step 1: Скрипт цепочки** — использует `spike/sora_lib.py` (`STYLE`, `create_video`, `poll_video`, `download_video`, `gen_image`).
  

Логика:

```python
# псевдо: реальный код в scripts/gen_scenes.py
from sora_lib import STYLE, create_video, poll_video, download_video, gen_image, OUT
import subprocess, sys
from pathlib import Path

def last_frame(mp4: Path, dst: Path):
    # надёжно: по индексу последнего кадра (nb_frames-1), не -sseof
    n = int(subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-count_frames","-show_entries","stream=nb_read_frames","-of","csv=p=0",str(mp4)],
        capture_output=True,text=True).stdout.strip())
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(mp4),
        "-vf",f"select=eq(n\\,{n-1})","-frames:v","1",str(dst)])
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(dst),
        "-vf","scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",str(dst)])

SCENES = [
  ("forest", "t2v", "Aerial drift over serene birch-and-pine forest 25km from the city, morning mist, a winding road toward a premium gated village in the distance. Settle into a slow forward glide.", "8"),
  ("gate",   "chain", "Continue the same slow forward drift, arriving at the village entrance: a stone stele 'Rodnaya Zemlya', clean modern gatehouse, allee of trees beginning. Keep gliding forward.", "8"),
  ("alley",  "chain", "Continue forward down the central landscaped alley: manicured greenery, amphitheatre, pond, families walking, 25 hectares of parkland. End settling toward a modern house.", "8"),
  ("house",  "anchor", "Slow cinematic descent toward this modern two-storey house by the water at golden hour, warm interior lights on, preserve exact architecture/materials/glazing of the reference. Settle drifting toward the glass facade.", "8"),
  ("interior","chain", "Continue forward through the floor-to-ceiling glass into a bright double-height living room: boucle sofa, stone fireplace, oak floors, marble kitchen island, dining with pendant lights. Keep gliding forward.", "8"),
  ("garden", "chain", "Continue forward out onto the terrace and garden: BBQ zone, fruit trees, water view, sunset calm. Settle to a gentle stop.", "8"),
]
```

Правила: `anchor` (house) — `ref=ref/voda_1280.png`; `chain` — `ref=<prev>_seed.png`; `t2v` — без ref. Все промпты с префиксом `STYLE`. После скачивания каждого — `last_frame(clip, ref/<next>_seed.png)`. Сцены генерятся **строго последовательно** (chain зависит от предыдущего). `interior` опционально: сначала `gen_image` брендового стилла, потом i2v (контроль мебели).

- [ ] 
  
  **Step 2: Прогнать генерацию**
  

Run: `cd /Users/fnt/work/sigius/myinfra/aool && python3 scripts/gen_scenes.py` Expected: `public/scroll/raw/forest.mp4 … garden.mp4` (6 клипов, 720p h264). Логи прогресса по каждой сцене.

- [ ] 
  
  **Step 3: Ревью связности (человеческий гейт)**
  

Собрать раскадровку всех 6 и открыть в snip. Если сцена вне стиля/с артефактами — перегенерить точечно (best-of-N: 2-3 попытки, брать лучшую). Не продолжать, пока мир не читается как единый.

Run: `python3 scripts/review_strip.py` (собирает `/tmp/scenes_overview.jpg`, `snip open`).

- [ ] 
  
  **Step 4: Коммит скриптов (без сырых mp4)**
  

```bash
git add scripts/gen_scenes.py && git commit -m "feat: sora-2 architecture-A scene chain generator"
```

* * *
## Task 2: Энкод для scroll-scrub (scroll-world Step 6)
**Files:** Create `scripts/encode.sh`

- [ ] 
  
  **Step 1: Скрипт энкода** — native-res, малый GOP, unsharp, faststart; + webm и webp-постеры.
  

`scripts/encode.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
raw=public/scroll/raw; out=public/scroll; mkdir -p "$out"
for f in "$raw"/*.mp4; do
  id=$(basename "$f" .mp4)
  ffmpeg -y -loglevel error -i "$f" -an -vf "unsharp=5:5:0.8:5:5:0.0" \
    -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p \
    -g 8 -keyint_min 8 -sc_threshold 0 -movflags +faststart "$out/$id.mp4"
  ffmpeg -y -loglevel error -i "$out/$id.mp4" -frames:v 1 "$out/$id.webp"   # постер/fallback
done
echo "encoded: $(ls "$out"/*.mp4 | wc -l) clips"
```

> Примечание: scroll-world требует именно `-g 8` + blob-seek (движок грузит клип как Blob → всегда seekable, byte-range не нужен). Не даунскейлить (у нас нативно 720p — потолок sora-2; апскейл до 1080p опционально в отдельном проходе `scale=1920:1080:flags=lanczos` ДО `-g8`, как в `spike/final`).

- [ ] 
  
  **Step 2: Прогнать**
  

Run: `bash scripts/encode.sh` Expected: `public/scroll/<id>.mp4` (≤ ~8МБ каждый) + `<id>.webp`.

- [ ] 
  
  **Step 3: Проверить seekability-настройки**
  

Run: `ffprobe -v error -show_entries stream=codec_name,width,height -show_entries format=duration public/scroll/forest.mp4` Expected: h264, 1280x720 (или 1920x1080 если апскейл), duration ~8s.

- [ ] 
  
  **Step 4: Коммит**
  

```bash
git add scripts/encode.sh public/scroll/*.webp && git commit -m "feat: scroll-scrub encode pipeline (-g8, unsharp, faststart)"
```

* * *
## Task 3: Next.js каркас + монтаж движка scroll-world
**Files:** scaffold; Create `components/ScrollWorld/{ScrollWorld.tsx,scenes.ts}`; copy `scrub-engine.js`

- [ ] 
  
  **Step 1: Scaffold**
  

Run:

```bash
cd /Users/fnt/work/sigius/myinfra/aool
npx create-next-app@latest . --ts --app --no-tailwind --no-src-dir --eslint --import-alias "@/*" --use-npm --no-turbopack
git add -A && git commit -m "chore: scaffold next.js app"
```

- [ ] 
  
  **Step 2: Копировать движок**
  

Run:

```bash
mkdir -p components/ScrollWorld
cp .claude/skills/scroll-world/references/scrub-engine.js components/ScrollWorld/scrub-engine.js
```

- [ ] 
  
  **Step 3: Конфиг сцен + копирайт**
  

`components/ScrollWorld/scenes.ts`:

```ts
export const scrollWorldConfig = {
  brand: { name: 'АУЛ', href: '#top' },
  hint: 'листайте — полёт начнётся',
  nav: true,
  crossfade: 0.12,
  connectors: [] as (string|null)[],   // Architecture A — коннекторов нет
  sections: [
    { id:'forest',   label:'Лес',        still:'/scroll/forest.webp',   clip:'/scroll/forest.mp4',
      accent:'#6a8a6b', eyebrow:'25 км от Уфы', title:'Тишина начинается здесь.',
      body:'Село Акбердино. Лес, воздух, покой.', tags:['Природа','Безопасность'] },
    { id:'gate',     label:'Въезд',      still:'/scroll/gate.webp',     clip:'/scroll/gate.mp4',
      accent:'#5a7a60', eyebrow:'Родная земля', title:'Пространство на традициях.', body:'Единый дизайн-код, безбарьерная среда.', tags:['Родство'] },
    { id:'alley',    label:'Аллея',      still:'/scroll/alley.webp',    clip:'/scroll/alley.mp4',
      accent:'#4a6a55', eyebrow:'25 гектаров', title:'103 дома, один ландшафт.', body:'Амфитеатр, пруд, беговые дорожки, сады.', tags:['Среда','Развитие'] },
    { id:'house',    label:'Дом',        still:'/scroll/house.webp',    clip:'/scroll/house.mp4',
      scroll:1.6, linger:0.4, accent:'#3a5a4a', eyebrow:'Дом «Вода»', title:'362 м², два этажа.', body:'Панорамное остекление, потолки 4,7 м.', tags:['Архитектура'] },
    { id:'interior', label:'Интерьер',   still:'/scroll/interior.webp', clip:'/scroll/interior.mp4',
      scroll:1.6, linger:0.45, accent:'#2d4a3e', eyebrow:'Внутри', title:'Свет и простор.', body:'Двусветная гостиная, камин, кухня-остров.', tags:['Комфорт'] },
    { id:'garden',   label:'Сад',        still:'/scroll/garden.webp',   clip:'/scroll/garden.mp4',
      scroll:1.4, linger:0.3, accent:'#2d4a3e', eyebrow:'Приватность', title:'Ваш собственный сад.', body:'Терраса, BBQ, фруктовые деревья.',
      tags:['Отдых'], cta:{ primary:{label:'Выбрать дом',href:'https://aool.space/doma/'}, secondary:{label:'О посёлке',href:'#manifesto'} } },
  ],
}
```

- [ ] 
  
  **Step 4: Клиентский компонент**
  

`components/ScrollWorld/ScrollWorld.tsx`:

```tsx
'use client'
import { useEffect, useRef } from 'react'
import { scrollWorldConfig } from './scenes'
// @ts-expect-error — vanilla engine, без типов
import { mountScrollWorld } from './scrub-engine.js'

export function ScrollWorld() {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (ref.current) mountScrollWorld(ref.current, scrollWorldConfig)
  }, [])
  return <div id="world" ref={ref} />
}
```

> Если `scrub-engine.js` использует `function mountScrollWorld(){}` без export — добавить в конец файла `export { mountScrollWorld }` (единственная правка вендорного файла).

- [ ] 
  
  **Step 5: Проверить сборку**
  

Run: `npm run build` Expected: `Compiled successfully`.

- [ ] 
  
  **Step 6: Коммит**
  

```bash
git add components/ScrollWorld/ && git commit -m "feat: mount scroll-world engine in next.js client component"
```

* * *
## Task 4: SSR-секции + сборка страницы
**Files:** Create `components/sections/*`; Modify `app/page.tsx`, `app/layout.tsx`

- [ ] 
  
  **Step 1: Секции** (Houses/Amenities/WhyAul/Manifesto/Cta/Footer) — SSR-контент из aool.space (каталог 4 домов, благоустройство, характеристики, манифест, CTA). Полный код — как в предыдущем плане `2026-07-10-...-plan-1-foundation.md` Task 7 (данные домов: Земля 226, Огонь 321, Воздух 428, Вода 362; цены от 38 млн).
  
- [ ] 
  
  **Step 2: Сборка**
  

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
      <Houses /><Amenities /><WhyAul /><Manifesto /><Cta /><Footer />
    </main>
  )
}
```

- [ ] 
  
  **Step 3: SEO metadata** — `app/layout.tsx` `metadata` (title/description/OG) из спеки.
  
- [ ] 
  
  **Step 4: Сборка + коммит**
  

```bash
npm run build && git add components/sections app/page.tsx app/layout.tsx && git commit -m "feat: SSR content sections and page assembly"
```

* * *
## Task 5: QA seam'ов и fallback (scroll-world Step 8)
**Files:** Create `playwright.config.ts`, `tests/e2e/scrollworld.spec.ts`

- [ ] 
  
  **Step 1: Playwright** — `npm i -D @playwright/test && npx playwright install chromium`; config с `webServer: build && start`.
  
- [ ] 
  
  **Step 2: Seam-QA тест** — скриншоты до/после каждого seam, сравнение near-identical; проверка `video.seekable.end(0) > 0` (blob работает); reduced-motion → постеры без видео; SSR-копия сцен в DOM.
  

`tests/e2e/scrollworld.spec.ts`:

```ts
import { test, expect } from '@playwright/test'

test('blob seekable (scrub works)', async ({ page }) => {
  await page.goto('/'); await page.mouse.wheel(0, 1500)
  const seek = await page.evaluate(() => { const v=document.querySelector('video'); return v && v.seekable.length ? v.seekable.end(0) : 0 })
  expect(seek).toBeGreaterThan(0)
})

test('SSR renders scene copy and content', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Тишина начинается здесь.')).toBeVisible()
  await expect(page.getByText('от 38 млн')).toBeVisible()
})

test('reduced-motion falls back to posters', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await ctx.newPage(); await page.goto('/')
  expect(await page.locator('img[src*="/scroll/"]').count()).toBeGreaterThan(0)
  await ctx.close()
})
```

- [ ] 
  
  **Step 3: Прогнать + визуальный seam-чек**
  

Run: `npm run e2e` (после `bash scripts/encode.sh`). Expected: тесты PASS. Дополнительно — вручную проскроллить, убедиться что стык 3↔4 (crossfade) без резкого «попа», стыки внутри якоря (4-5-6) бесшовны.

- [ ] 
  
  **Step 4: Коммит**
  

```bash
git add playwright.config.ts tests/e2e && git commit -m "test: seam QA, blob-seek, reduced-motion fallback"
```

* * *
## Task 6: Деплой в AKS (GitOps)
**Files:** Create `Dockerfile`, `.dockerignore`; ArgoCD Application в `infra/`

- [ ] 
  
  **Step 1: Multi-stage Dockerfile** (Next.js standalone output). `next.config.mjs`: `output: 'standalone'`.
  
- [ ] 
  
  **Step 2: CI** — reusable Kaniko build (`sigiuscom/workflows/.github/workflows/docker-build.yml`), добавить репо по `infra/github-actions-runners/README.md`.
  
- [ ] 
  
  **Step 3: ArgoCD Application** — манифест в `infra/argocd/applications/aool-landing.yaml`, namespace `aool-landing`, ClusterIP; проксирование через NPM (домен позже). Ассеты `public/scroll/*.mp4` — в образ (или отдельный volume/CDN, если вес критичен).
  
- [ ] 
  
  **Step 4: Push → ArgoCD auto-sync.** Проверить `kubectl get application aool-landing -n argocd`.
  

> Деплой — отдельная итерация; сначала Tasks 1-5 дают работающий лендинг локально.

* * *
## Definition of Done
- 6 leg-клипов сгенерены, связный мир (человеческий ревью пройден), артефакты в пределах согласованного.
  
- `npm run build` зелёный; `npm run e2e` проходит; seam'ы визуально чистые (якорь бесшовен, стык стрелка↔якорь через crossfade без «попа»).
  
- Лендинг открывается: scroll-пролёт + копирайт-оверлеи + SSR-секции; reduced-motion → постеры.
  
- (Опц.) Задеплоено в AKS через ArgoCD.
  
## Открытые риски
- Артефакты Sora на выразительных движениях → best-of-N, медленнее камера, remix проблемных.
  
- Вес ассетов (6×~8МБ) → lazy-load движка + возможный CDN для `public/scroll/`.
  
- Стык стрелка↔якорь: если crossfade заметен — вставить короткий i2v-переход аллея→дом как доп. leg.
