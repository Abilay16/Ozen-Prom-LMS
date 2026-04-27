# Özen Prom LMS

> Корпоративная система дистанционного обучения (LMS) для промышленного предприятия.  
> Обучение сотрудников, тестирование знаний по охране труда и промышленной безопасности, контроль результатов.

![Vue 3](https://img.shields.io/badge/Vue-3.4-42b883?logo=vue.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker&logoColor=white)

---

## Скриншоты

> _Скриншоты будут добавлены в ближайшее время_

---

## Возможности

### Администратор
- Управление организациями, дисциплинами, курсами и материалами (PDF, видео, изображения, Word, ссылки)
- Создание тестов с вопросами и вариантами ответов
- Управление пользователями и потоками обучения
- Правила назначения курсов по должности / дисциплине
- **Excel-импорт сотрудников** — загрузка списка с превью и автоматическим назначением курсов
- Экспорт прогресса в Excel
- Сброс паролей

### Ученик (learner)
- Личный кабинет с назначенными курсами
- Просмотр материалов прямо в браузере (PDF, видео-стриминг, изображения)
- Прохождение тестов с попытками и результатами
- История тестирования

---

## Технологии

| Слой | Технологии |
|---|---|
| Backend | FastAPI 0.115, SQLAlchemy 2 (async), Alembic, PostgreSQL 15 |
| Frontend | Vue 3.4, Vite 5, Tailwind CSS 3, Pinia, Axios |
| Auth | JWT (access + refresh tokens), bcrypt |
| Excel | pandas + openpyxl |
| Видео | Nginx X-Accel-Redirect (стриминг с поддержкой Range) |
| Инфраструктура | Docker Compose, Nginx, Let's Encrypt (SSL) |

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
# На сервере: клонировать и настроить
git clone https://github.com/Abilay16/Ozen-Prom-LMS.git /opt/ozen-lms
cd /opt/ozen-lms
cp .env.example .env
# Заполнить .env: POSTGRES_PASSWORD, SECRET_KEY, ALLOWED_ORIGINS

# Запустить прод-стек
docker compose -f docker-compose.prod.yml up -d --build
```

### SSL (Let's Encrypt)

```bash
# Остановить nginx, получить сертификат
systemctl stop nginx
certbot certonly --standalone -d yourdomain.com
# Скопировать сертификаты
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/certs/
# Запустить
docker compose -f docker-compose.prod.yml up -d
```

### Создать первого администратора

```bash
docker compose -f docker-compose.prod.yml exec backend python -m scripts.seed_admin
```

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
