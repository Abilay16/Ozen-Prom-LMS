import { test, expect } from '@playwright/test'
import { login, watchErrors } from './helpers.js'

test('обучающийся проходит тест и получает «Тест сдан»', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'learner')
  await expect(page).toHaveURL(/\/my\/courses/)

  await page.getByRole('link', { name: /E2E курс/ }).click()
  await expect(page).toHaveURL(/\/my\/courses\/.+/)

  await page.getByRole('button', { name: 'Начать тест' }).click()
  await expect(page).toHaveURL(/\/my\/test\/.+/)

  const correct = page.getByText('Верно', { exact: true })
  await expect(correct).toHaveCount(3)
  await correct.nth(0).click()

  // Сдача с пропущенными вопросами — сначала предупреждение, можно вернуться.
  await page.getByRole('button', { name: 'Завершить тест' }).click()
  await expect(page.getByText(/Нет ответа на вопросы № 2, 3/)).toBeVisible()
  await page.getByRole('button', { name: 'Вернуться к вопросам' }).click()

  await correct.nth(1).click()

  // Перезагрузка посреди теста не стирает выбранные ответы.
  await page.reload()
  await expect(page.getByText('2 / 3 ответов')).toBeVisible()
  await correct.nth(2).click()
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
