import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

// Перед каждым прогоном пересоздаём тестовые данные (в т.ч. сбрасываем
// пройденный тест обучающегося). В CI команду задаёт E2E_SEED_CMD;
// локально — через docker compose из корня репозитория.
export default function globalSetup() {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..')
  const cmd = process.env.E2E_SEED_CMD || 'docker compose exec -T backend python -m scripts.seed_e2e'
  execSync(cmd, { cwd: root, stdio: ['ignore', 'ignore', 'inherit'] })
}
