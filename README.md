# Ozen-Prom LMS

Корпоративная LMS-система для Оzen Prom — обучение, тестирование и контроль знаний сотрудников в сфере промышленной безопасности.

---

## Стек

| Слой | Технологии |
|---|---|
| Backend | FastAPI 0.115, SQLAlchemy 2 (async), Alembic, PostgreSQL 15 |
| Frontend | Vue 3.4, Vite 5, Tailwind CSS 3.4, Pinia, Axios |
| Auth | JWT (access + refresh), bcrypt |
| Excel | pandas + openpyxl |
| Инфраструктура | Docker Compose, Nginx |

---

## Быстрый старт (DEV)

### 1. Клонировать и настроить переменные

```bash
git clone https://github.com/Abilay16/Ozen-Prom-LMS.git
cd "Ozen-Prom-LMS"
cp .env.example .env
# Отредактируйте .env — задайте SECRET_KEY и пароль БД
```

### 2. Запустить контейнеры

```bash
docker compose up -d --build
```

Сервисы:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1
- Swagger UI: http://localhost:8000/docs

### 3. Создать первого администратора

```bash
docker compose exec backend python -m scripts.seed_admin
```

### 4. Создать первую миграцию

```bash
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
```

---

## Структура проекта

```
.
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Роуты FastAPI
│   │   ├── core/            # Config, Database, Security
│   │   ├── models/          # SQLAlchemy модели
│   │   ├── services/        # Бизнес-логика
│   │   └── utils/           # Транслитерация
│   ├── alembic/             # Миграции БД
│   └── scripts/             # seed_admin.py
├── frontend/
│   └── src/
│       ├── pages/           # Vue-страницы (public / learner / admin)
│       ├── layouts/         # PublicLayout, LearnerLayout, AdminLayout
│       ├── stores/          # Pinia (auth)
│       └── services/        # Axios-клиент
├── docker/nginx/            # Конфиги Nginx
├── storage/                 # Файлы (не коммитятся)
├── docker-compose.yml       # DEV
└── docker-compose.prod.yml  # PROD
```

---

## Деплой на продакшн (VPS)

```bash
# Скопировать .env.prod и настроить
cp .env.example .env
# Поднять прод-стек
docker compose -f docker-compose.prod.yml up -d --build
```

Nginx слушает порт 80. SSL добавляется через Let's Encrypt (Certbot) — конфиг закомментирован в `docker/nginx/nginx.prod.conf`.

---

## Роли

| Роль | Описание |
|---|---|
| `admin` | Полный доступ: CRUD пользователей, потоков, курсов, тестов, экспорт |
| `learner` | Доступ к своим курсам, материалам и тестам |

---

## Excel-импорт

Формат файла: `.xlsx`, обязательные колонки (гибкое сопоставление):
- **ФИО** (или `full_name`, `Фамилия Имя`, `ФИО`)
- **Должность** (или `position`, `Должность`)
- **Дисциплина** (или `discipline`, `Направление`)

Алгоритм: загрузка → превью (OK / На проверку / Ошибки) → подтверждение → создание пользователей + назначение курсов по правилам.

---

## Лицензия

Proprietary — ТОО Özen Prom
