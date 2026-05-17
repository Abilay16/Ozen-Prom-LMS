# Полный аудит кодовой базы — Ozen-Prom LMS
_Составлен: 2026-05-11_

---

## Статус: что уже сделано ✅
- deps.py: `CurrentAdmin` / `CurrentSuperAdmin` — разделение ролей
- auth.py: `is_commission` в `TokenResponse`
- training_types.py: GET → CurrentAdmin, POST/PATCH → CurrentSuperAdmin
- batches.py: GET → CurrentAdmin, мутации → CurrentSuperAdmin
- admin_users.py: GET → CurrentAdmin, POST/PATCH → CurrentSuperAdmin, dead code удалён
- protocols.py: все 11 мутаций → CurrentSuperAdmin, чтение/подпись → CurrentAdmin
- AdminLayout.vue: mobile sidebar overlay, commission-aware nav
- ProtocolsPage.vue: кнопка "+ Новый протокол" скрыта для комиссии
- router/index.js: /admin/protocols/new заблокирован для комиссии
- 20/20 тестов проходят

---

## Найденные проблемы — бэкенд

### B1 ⚠️ HIGH — auth.py: `last_login` никогда не сохраняется
**Файл:** `backend/app/api/v1/auth.py`  
**Проблема:** В `login()` и `refresh_token()` устанавливается `admin.last_login = ...` и
`user.last_login = ...`, но `await db.commit()` после этого не вызывается.
SQLAlchemy объект помечается "dirty", но транзакция не фиксируется → last_login всегда NULL.  
**Фикс:** добавить `await db.commit()` перед возвратом для каждой ветки.

---

### B2 ⚠️ MEDIUM — batches.py: неправильный порядок параметров в `upload_excel`
**Файл:** `backend/app/api/v1/batches.py`  
**Проблема:**
```python
async def upload_excel(batch_id: UUID, file: UploadFile = File(...), db: DB = None, admin: CurrentSuperAdmin = None):
```
`db` и `admin` объявлены с `= None` — FastAPI injektирует их через Annotated-метаданные,
поэтому runtime работает, но `db: DB = None` вводит в заблуждение, ломает статический анализ
и нарушает соглашение (всегда: зависимости без дефолтного значения, файл с `= File(...)`).  
**Фикс:** переставить параметры: `batch_id: UUID, db: DB, admin: CurrentSuperAdmin, file: UploadFile = File(...)`.

---

### B3 🔵 LOW — admin_users.py: избыточная проверка прав
**Файл:** `backend/app/api/v1/admin_users.py`, строка ~65  
**Проблема:** `create_admin_user` уже защищён `CurrentSuperAdmin`, но дополнительно проверяет
`if not admin.is_superadmin: raise ForbiddenError(...)`. Это мёртвый код — никогда не сработает.  
**Фикс:** удалить лишние 2 строки.

---

## Найденные проблемы — фронтенд

### F1 ⚠️ HIGH — ProtocolDetailPage.vue: комиссия видит все кнопки редактирования
**Файл:** `frontend/src/pages/admin/ProtocolDetailPage.vue`  
**Проблема:** Логика `isDraft` блокирует поля только для archived/signed/awaiting_signatures статусов.
Когда комиссионер открывает **черновой** протокол:
- все поля формы активны (`isDraft = true`)
- кнопки "Сохранить", "Отправить на подпись", "Добавить члена комиссии",
  "✕ удалить члена", "⬇ Загрузить из потока", "+ Добавить вручную" — видны и кликабельны
- бэкенд вернёт 403, но UX сломан  

Когда комиссионер открывает **подписанный** протокол:
- кнопка "Архивировать" видна, бэкенд вернёт 403  

**Фикс:** `const isCommission = localStorage.getItem('is_commission') === '1'` и
добавить `v-if="!isCommission"` на все кнопки мутации — сохранить, удалить, импортировать,
отправить на подпись, архивировать.  
Комиссионер должен видеть только панель «Статус + Подписать».

---

### F2 ⚠️ MEDIUM — CommissionPage.vue: поля редактирования для комиссионера
**Файл:** `frontend/src/pages/admin/CommissionPage.vue`  
**Проблема:** Комиссионер может открыть `/admin/commission`, видит input и checkbox,
пытается редактировать — PATCH вернёт 403. Плохой UX.  
**Фикс:** если `isCommission === true`, отключить inputs/checkboxes и показать баннер read-only.

---

### F3 ⚠️ MEDIUM — api.js: авторефреш не сохраняет `is_commission`
**Файл:** `frontend/src/services/api.js`  
**Проблема:** В interceptor при 401-рефреше
`localStorage.setItem('access_token', data.access_token)` — других полей нет.
Если статус комиссии изменится, `is_commission` в localStorage останется устаревшим.  
**Фикс:** добавить сохранение `is_commission`, `full_name`, `role` в refresher.

---

### F4 🔵 LOW — ProtocolDetailPage.vue: печать для комиссии не блокирует редактирование на мобиле
**Статус:** несущественно с текущим мобильным сайдбаром.

---

### F5 🔵 INFO — Нет пагинации на ProtocolsPage
Списки протоколов и удостоверений ограничены 50 записями без кнопки "ещё".
Достаточно для текущего масштаба. Отметить для будущего.

---

## План фиксов (приоритет сверху вниз)

| # | Файл | Проблема | Сложность |
|---|------|----------|-----------|
| 1 | auth.py | last_login не коммитится | S |
| 2 | batches.py | upload_excel параметры | XS |
| 3 | admin_users.py | мёртвый код | XS |
| 4 | ProtocolDetailPage.vue | кнопки для комиссии | M |
| 5 | CommissionPage.vue | read-only для комиссии | S |
| 6 | api.js | refresh + is_commission | XS |

---

## Состояние разрешений по эндпоинтам (финальное)

| Router | Method | Path | Required role |
|--------|--------|------|---------------|
| protocols | GET | / | CurrentAdmin |
| protocols | GET | /commission-candidates | CurrentAdmin |
| protocols | GET | /{id} | CurrentAdmin |
| protocols | GET | /{id}/signature-payload | CurrentAdmin |
| protocols | POST | /{id}/sign | CurrentAdmin |
| protocols | POST | / | CurrentSuperAdmin |
| protocols | PATCH | /{id} | CurrentSuperAdmin |
| protocols | DELETE | /{id} | CurrentSuperAdmin |
| protocols | POST | /{id}/commission | CurrentSuperAdmin |
| protocols | DELETE | /{id}/commission/{mid} | CurrentSuperAdmin |
| protocols | POST | /{id}/request-signatures | CurrentSuperAdmin |
| protocols | POST | /{id}/participants | CurrentSuperAdmin |
| protocols | PATCH | /{id}/participants/{pid} | CurrentSuperAdmin |
| protocols | DELETE | /{id}/participants/{pid} | CurrentSuperAdmin |
| protocols | POST | /{id}/import-participants | CurrentSuperAdmin |
| protocols | POST | /{id}/issue-certificates | CurrentSuperAdmin |
| training_types | GET | / | CurrentAdmin |
| training_types | POST | / | CurrentSuperAdmin |
| training_types | PATCH | /{id} | CurrentSuperAdmin |
| batches | GET | / | CurrentAdmin |
| batches | GET | /{id} | CurrentAdmin |
| batches | POST | / | CurrentSuperAdmin |
| batches | DELETE | /{id} | CurrentSuperAdmin |
| batches | POST | /{id}/upload-excel | CurrentSuperAdmin |
| batches | POST | /{id}/preview-import | CurrentSuperAdmin |
| batches | POST | /{id}/confirm-import | CurrentSuperAdmin |
| admin_users | GET | / | CurrentAdmin |
| admin_users | POST | / | CurrentSuperAdmin |
| admin_users | PATCH | /{id} | CurrentSuperAdmin |
| certificates | GET | / | CurrentAdmin |
| certificates | GET | /{id} | CurrentAdmin |
| certificates | POST | / | CurrentSuperAdmin |
| certificates | PATCH | /{id} | CurrentSuperAdmin |
| certificates | DELETE | /{id} | CurrentSuperAdmin |
| users (learner) | all | / | CurrentSuperAdmin as CurrentAdmin |
| progress | all | / | CurrentSuperAdmin as CurrentAdmin |
| exports | all | / | CurrentSuperAdmin as CurrentAdmin |
| disciplines | all | / | CurrentSuperAdmin as CurrentAdmin |
| positions | all | / | CurrentSuperAdmin as CurrentAdmin |
| courses | all | / | CurrentSuperAdmin as CurrentAdmin |
| rules | all | / | CurrentSuperAdmin as CurrentAdmin |
| organizations | all | / | CurrentSuperAdmin as CurrentAdmin |

---

## Состояние фронтового роутинга для комиссии

Разрешены: `/admin/protocols/*`, `/admin/commission`, `/admin/certificates/*`  
Заблокированы (→ redirect /admin/protocols):
- `/admin/dashboard`
- `/admin/batches/*`
- `/admin/users`
- `/admin/courses/*`
- `/admin/disciplines`
- `/admin/positions`
- `/admin/progress`
- `/admin/exports`
- `/admin/protocols/new` (явная проверка перед startsWith)
