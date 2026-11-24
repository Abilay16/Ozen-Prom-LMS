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

test('сертификат БиОТ ИТР: штамп ЭЦП и скачивание PDF файлом', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'learner')
  await page.goto('/my/certificates/00000000-0000-4000-8000-00000000e2e2')
  await expect(page.locator('.biot-cert .stamp')).toBeVisible()
  await expect(page.locator('.biot-cert')).toContainText('E2E0SERIAL0001')

  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Скачать PDF' }).click()
  const file = await download
  expect(file.suggestedFilename()).toBe('Сертификат_E2E-BIOT-ITR-1.pdf')
  const fs = await import('node:fs')
  const bytes = fs.readFileSync(await file.path())
  expect(bytes.subarray(0, 5).toString()).toBe('%PDF-')
  expect(bytes.length).toBeGreaterThan(100_000) // картинка листа, а не пустой файл
  guard.check()
})

test('карта работника: новый макет, скачивание PDF', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'learner')
  await page.goto('/my/certificates')
  await page.getByRole('button', { name: 'Карта работника' }).click()
  const card = page.locator('.worker-card')
  await expect(card).toContainText('Тестов')
  await expect(card).toContainText('Тест Тестович')
  await expect(card.locator('img.qr')).toBeVisible()

  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Скачать PDF' }).click()
  const file = await download
  expect(file.suggestedFilename()).toBe('Карта_Тестов_Тест_Тестович.pdf')
  const fs = await import('node:fs')
  expect(fs.readFileSync(await file.path()).subarray(0, 5).toString()).toBe('%PDF-')
  guard.check()
})

test('обучающемуся закрыта админка', async ({ page }) => {
  await login(page, 'learner')
  await page.goto('/admin/dashboard')
  await expect(page).not.toHaveURL(/\/admin\/dashboard/)
})
