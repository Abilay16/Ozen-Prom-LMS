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

test('суперадмин скачивает сертификат БиОТ ИТР файлом, а не уходит на печать', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'admin')
  await page.goto('/admin/certificates/00000000-0000-4000-8000-00000000e2e2')
  await expect(page.locator('.biot-cert .stamp')).toBeVisible()
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Скачать PDF' }).click()
  expect((await download).suggestedFilename()).toBe('Сертификат_E2E-BIOT-ITR-1.pdf')
  await expect(page).toHaveURL(/\/admin\/certificates\//)
  guard.check()
})

test('протокол: печать → «Назад к протоколу» → «Назад» ведёт к списку, а не на печать', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'admin')
  await page.goto('/admin/protocols')
  await page.getByText('E2E-П-1').first().click()
  await expect(page).toHaveURL(/\/admin\/protocols\/[0-9a-f-]+$/)
  await page.getByRole('button', { name: /Печать протокола/ }).click()
  await expect(page).toHaveURL(/\/print$/)
  await page.getByRole('button', { name: /Назад к протоколу/ }).click()
  await expect(page).toHaveURL(/\/admin\/protocols\/[0-9a-f-]+$/)
  await page.getByRole('button', { name: /^← Назад$/ }).click()
  await expect(page).toHaveURL(/\/admin\/protocols$/)
  guard.check()
})

test('дисциплины: в архив, новая с тем же кодом создаётся отдельно', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'admin')
  await page.goto('/admin/disciplines')
  const code = `ARCH${Date.now() % 100000}`
  const main = page.locator('main')

  async function create(name) {
    await main.getByRole('button', { name: '+ Добавить' }).click()
    const dialog = page.getByRole('dialog')
    await dialog.locator('input').nth(0).fill(code)
    await dialog.locator('input').nth(1).fill(name)
    await dialog.getByRole('button', { name: 'Сохранить' }).click()
    await expect(main.getByRole('row', { name: new RegExp(name) })).toBeVisible()
  }
  async function archive(name) {
    await main.getByRole('row', { name: new RegExp(name) }).getByRole('button', { name: 'В архив' }).click()
    await page.getByRole('alertdialog').getByRole('button', { name: 'В архив' }).click()
    await expect(main.getByRole('row', { name: new RegExp(name) })).toHaveCount(0)
  }

  await create('Старая E2E')
  await archive('Старая E2E')
  await create('Новая E2E')  // раньше вместо новой «оживала» старая

  await page.getByRole('tab', { name: 'Архив' }).click()
  await expect(main.getByRole('row', { name: /Старая E2E/ }).first()).toBeVisible()
  await expect(main.getByRole('row', { name: /Новая E2E/ })).toHaveCount(0)

  // Вернуть старую нельзя, пока действует новая с тем же кодом.
  await main.getByRole('row', { name: /Старая E2E/ }).first().getByRole('button', { name: 'Вернуть' }).click()
  await expect(page.getByText(/уже есть/)).toBeVisible()

  await page.getByRole('tab', { name: 'Действующие' }).click()
  await archive('Новая E2E')
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

test('прогресс: одна строка на сотрудника, по нажатию — его обучения', async ({ page }) => {
  const guard = watchErrors(page)
  await login(page, 'admin')
  await page.goto('/admin/progress')
  const person = page.getByRole('button', { name: /Тестов Тест Тестович/ })
  await expect(person).toHaveCount(1)
  await expect(person).toHaveAttribute('aria-expanded', 'false')
  await person.click()
  await expect(person).toHaveAttribute('aria-expanded', 'true')
  // Подробности свёрстаны отдельно для телефона и компьютера — берём видимые.
  await expect(page.getByText('E2E курс').filter({ visible: true })).toHaveCount(1)
  guard.check()
})
