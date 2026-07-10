import { test, expect } from '@playwright/test'

test('page loads with SEO metadata and content in DOM', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/Посёлок АУЛ/)
  // SEO-контент присутствует в DOM (visually-hidden)
  await expect(page.getByText('от 38 млн', { exact: false })).toBeAttached()
  await expect(page.getByRole('heading', { name: /Почему АУЛ/ })).toBeAttached()
})

test('scroll-world engine mounts and video blob is seekable', async ({ page }) => {
  await page.goto('/')
  await page.waitForTimeout(1500)
  const seekable = await page.evaluate(() => {
    const v = document.querySelector('video')
    return v && v.seekable.length ? v.seekable.end(0) : 0
  })
  expect(seekable).toBeGreaterThan(0) // blob-seek работает (не byte-range)
})

test('scroll drives video currentTime (scrub)', async ({ page }) => {
  await page.goto('/')
  await page.waitForTimeout(1200)
  await page.evaluate(() => window.scrollTo(0, window.innerHeight * 2.2))
  await page.waitForTimeout(800)
  const t = await page.evaluate(() => document.querySelector('video')?.currentTime ?? 0)
  expect(t).toBeGreaterThan(1)
})

test('primary CTA is visible with contrasting text', async ({ page }) => {
  await page.goto('/')
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
  await page.waitForTimeout(800)
  const btn = page.locator('.sw-btn--primary')
  await expect(btn).toBeVisible()
  const { color, bg } = await btn.evaluate((el) => {
    const cs = getComputedStyle(el)
    return { color: cs.color, bg: cs.backgroundColor }
  })
  expect(color).not.toBe(bg) // текст не сливается с фоном
})

test('reduced-motion falls back to still posters', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await ctx.newPage()
  await page.goto('/')
  await page.waitForTimeout(800)
  const stills = await page.locator('img[src*="/scroll/"]').count()
  expect(stills).toBeGreaterThan(0)
  await ctx.close()
})
