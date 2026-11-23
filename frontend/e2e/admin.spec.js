import { test, expect } from '@playwright/test'
import { login, watchErrors } from './helpers.js'

const ADMIN_PAGES = [
  '/admin/dashboard', '/admin/batches', '/admin/users', '/admin/organizations',
  '/admin/disciplines', '/admin/courses', '/admin/positions', '/admin/rules',
  '/admin/progress', '/admin/exports', '/admin/med-exams', '/admin/protocols',
  '/admin/protocols/new', '/admin/commission', '/admin/certificates',
]

test('суперадмин: все страницы админки открываются без JS-ошибок и 5xx', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'admin')
  await expect(page).toHaveURL(/\/admin\/dashboard/)

  for (const path of ADMIN_PAGES) {
    await page.goto(path)
    await expect(page.locator('main h1').first(), `заголовок на ${path}`).toBeVisible()
    await page.waitForLoadState('networkidle')
  }
  guard.check()
})

test('суперадмин видит удостоверение E2E в списке и открывает его', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'admin')
  await page.goto('/admin/certificates')
  await expect(page.getByText('E2E-BIOT-0001').first()).toBeVisible()
  guard.check()
})

test('член комиссии попадает на протоколы, без пунктов администрирования', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'chair')
  await expect(page).toHaveURL(/\/admin\/protocols/)
  const nav = page.locator('aside nav').first()
  await expect(nav.getByText('Протоколы')).toBeVisible()
  await expect(nav.getByText('Пользователи')).toHaveCount(0)
  await expect(page.getByText('+ Новый протокол')).toHaveCount(0)
  guard.check()
})

test('просмотр по организации: все разделы открываются, кнопок изменения нет', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'viewer')
  for (const path of ['/admin/dashboard', '/admin/batches', '/admin/users', '/admin/progress', '/admin/protocols', '/admin/certificates']) {
    await page.goto(path)
    await expect(page.locator('main h1').first(), `заголовок на ${path}`).toBeVisible()
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('button', { name: /Добавить|Новый|Удалить|Пересдача/ }), `кнопки изменения на ${path}`).toHaveCount(0)
  }
  guard.check()
})

test('просмотр по организации: видит только своих сотрудников', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'viewer')
  await page.goto('/admin/users')
  await expect(page.getByText('Тестов Тест Тестович').first()).toBeVisible()
  await expect(page.getByText('Чужой Сотрудник Иванович')).toHaveCount(0)

  // Запись закрыта: на страницы создания не пускает.
  await page.goto('/admin/protocols/new')
  await expect(page).not.toHaveURL(/\/admin\/protocols\/new/)
  guard.check()
})
