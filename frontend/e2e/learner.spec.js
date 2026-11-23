import { test, expect } from '@playwright/test'
import { login, watchErrors } from './helpers.js'

test('обучающийся проходит тест и получает «Тест сдан»', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'learner')
  await expect(page).toHaveURL(/\/my\/courses/)

  const card = page.locator('.card', { hasText: 'E2E курс' })
  await card.getByText('Перейти к курсу').click()
  await expect(page).toHaveURL(/\/my\/courses\/.+/)

  await page.getByRole('button', { name: 'Начать тест' }).click()
  await expect(page).toHaveURL(/\/my\/test\/.+/)

  const correct = page.getByText('Верно', { exact: true })
  await expect(correct).toHaveCount(3)
  for (let i = 0; i < 3; i++) await correct.nth(i).click()
  await expect(page.getByText('3 / 3 ответов')).toBeVisible()

  await page.getByRole('button', { name: 'Завершить тест' }).click()
  await expect(page.getByText('Тест сдан!')).toBeVisible()
  guard.check()
})

test('обучающийся видит свои удостоверения', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'learner')
  await page.goto('/my/certificates')
  await expect(page.getByText('E2E-BIOT-0001').first()).toBeVisible()
  guard.check()
})

test('обучающемуся закрыта админка', async ({ page }) => {
  await login(page, 'learner')
  await page.goto('/admin/dashboard')
  await expect(page).not.toHaveURL(/\/admin\/dashboard/)
})
