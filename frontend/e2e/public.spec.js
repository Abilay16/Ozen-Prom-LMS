import { test, expect } from '@playwright/test'
import { CERT_ID, watchErrors } from './helpers.js'

test('публичные страницы открываются без ошибок', async ({ page }) => {
  const guard = watchErrors(page)
  for (const path of ['/', '/about', '/services', '/contacts', '/faq']) {
    await page.goto(path)
    await expect(page.locator('body')).not.toBeEmpty()
  }
  await page.goto('/no-such-page')
  await expect(page.getByText('404')).toBeVisible()
  guard.check()
})

test('проверка удостоверения по QR показывает статус и ФИО', async ({ page }) => {
  const guard = watchErrors(page)
  await page.goto(`/verify/${CERT_ID}`)
  await expect(page.getByText('Удостоверение действительно')).toBeVisible()
  await expect(page.getByText('Тестов Тест Тестович').first()).toBeVisible()
  guard.check()
})

test('несуществующее удостоверение — «Недействительно»', async ({ page }) => {
  await page.goto('/verify/00000000-0000-4000-8000-000000000000')
  await expect(page.getByText('Недействительно')).toBeVisible()
})

test('неверный пароль — понятная ошибка, остаёмся на входе', async ({ page }) => {
  await page.goto('/login')
  // Отдельный логин: неудачные попытки копятся в защите от подбора пароля.
  await page.locator('#login').fill('e2e_wrong_password_check')
  await page.locator('#password').fill('wrong-password')
  await page.getByRole('button', { name: 'Войти' }).click()
  await expect(page.locator('.login-screen')).toContainText(/неверн|слишком много/i)
  await expect(page).toHaveURL(/\/login/)
})

test('без входа кабинет и админка редиректят на вход', async ({ page }) => {
  await page.goto('/admin/dashboard')
  await expect(page).toHaveURL(/\/login/)
  await page.goto('/my/courses')
  await expect(page).toHaveURL(/\/login/)
})
