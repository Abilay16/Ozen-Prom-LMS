import { expect } from '@playwright/test'

export const USERS = {
  admin: { login: 'e2e_admin', password: 'E2e-Admin-123' },
  chair: { login: 'e2e_chair', password: 'E2e-Chair-123' },
  viewer: { login: 'e2e_viewer', password: 'E2e-View-123' },
  learner: { login: 'e2e_learner', password: 'E2e-Learn-123' },
}

export const CERT_ID = '00000000-0000-4000-8000-00000000e2e1'

export async function login(page, who) {
  const { login, password } = USERS[who]
  await page.goto('/login')
  await page.locator('#login').fill(login)
  await page.locator('#password').fill(password)
  await page.getByRole('button', { name: 'Войти' }).click()
  await page.waitForURL(url => !url.pathname.startsWith('/login'))
}

/**
 * Собирает JS-ошибки страницы и ответы API 5xx/403 — любой из них валит тест.
 * Вызвать до действий, в конце — `await guard.check()`.
 */
export function watchErrors(page) {
  const errors = []
  page.on('pageerror', e => errors.push(`pageerror: ${e.message}`))
  page.on('response', r => {
    // 5xx — сломан бэкенд; 403 — интерфейс сам ходит туда, куда этой роли нельзя.
    if (r.url().includes('/api/') && (r.status() >= 500 || r.status() === 403)) {
      errors.push(`${r.status()} ${r.request().method()} ${r.url()}`)
    }
  })
  return {
    errors,
    check: () => expect(errors, errors.join('\n')).toEqual([]),
  }
}
