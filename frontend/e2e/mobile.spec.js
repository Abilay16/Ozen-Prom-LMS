import { test, expect } from '@playwright/test'
import { CERT_ID, login, watchErrors } from './helpers.js'

test('телефон: нет горизонтальной прокрутки на ключевых страницах', async ({ page }) => {
  const guard = watchErrors(page)
  const noHScroll = async (label) => {
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow, `горизонтальная прокрутка на ${label}`).toBeLessThanOrEqual(1)
  }
  await page.goto('/')
  await noHScroll('/')
  await page.goto(`/verify/${CERT_ID}`)
  await expect(page.getByText('Удостоверение действительно')).toBeVisible()
  await noHScroll('/verify')
  await login(page, 'learner')
  await noHScroll('/my/courses')
  guard.check()
})
