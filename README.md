# AI Backend Contact Service

Backend-сервис формы обратной связи для лендинга разработчика. Обращение
валидируется, анализируется через OpenAI, сохраняется в PostgreSQL, после чего
сервис независимо отправляет уведомления владельцу и пользователю.

Если OpenAI или SMTP недоступны, обращение не теряется: API сохраняет его и
возвращает статусы fallback/failed.

В репозитории также находится минимальный адаптивный frontend: лендинг,
форма обратной связи, отображение результата отправки и индикатор состояния API.
Frontend обслуживается самим FastAPI-приложением и не требует отдельной сборки.

## Стек

- Python 3.13+
- FastAPI, Pydantic v2
- SQLAlchemy 2.x Async, asyncpg, PostgreSQL
- Alembic
- OpenAI Responses API
- aiosmtplib
- Docker, Docker Compose
- HTML5, CSS3, JavaScript без frontend-фреймворка

## Архитектура

```text
HTTP router
    -> ContactService
        -> AIService
        -> ContactRepository
        -> EmailService
        -> ContactRepository
```

- `backend/api` — HTTP-контракт и FastAPI dependencies.
- `backend/services` — orchestration и интеграции AI/SMTP.
- `backend/repositories` — операции сохранения.
- `backend/db/models` — SQLAlchemy-модели.
- `backend/schemas` — Pydantic DTO.
- `backend/core` — конфигурация, логирование, rate limit и обработка ошибок.
- `backend/static` — лендинг и клиентская интеграция с REST API.

Router не содержит бизнес-логики. `AsyncSession` создается на запрос и передается
в repository через Dependency Injection.

## Локальный запуск

### 1. Клонирование репозитория

Для клонирования проекта необходим установленный Git:

```powershell
git clone https://github.com/filipenkovmaksim30-tech/ai_backend_service.git
cd ai_backend_service
```

### 2. Подготовка окружения

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Отредактируйте `.env`. Для локального PostgreSQL из Compose используется порт
`5433`, чтобы не конфликтовать с установленным PostgreSQL на `5432`.

### 3. PostgreSQL и миграции

```powershell
docker compose up -d postgres
alembic upgrade head
```

### 4. API

```powershell
uvicorn backend.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`
- Лендинг: `http://127.0.0.1:8000/`

Полный запуск через Docker:

```powershell
docker compose up --build
```

API-контейнер ожидает готовность PostgreSQL и автоматически применяет миграции.

## Frontend

Frontend намеренно реализован без React/Vue и отдельного Node.js toolchain.
Для небольшого одностраничного лендинга это уменьшает количество зависимостей,
ускоряет локальный запуск и позволяет отдавать UI и API из одного контейнера.

Форма отправляет JSON в `POST /api/contact` и обрабатывает:

- успешный ответ `201`;
- ошибки валидации `422`;
- превышение rate limit `429` с учетом заголовка `Retry-After`;
- временную недоступность сервиса `503`;
- сетевые и непредвиденные ошибки;
- AI fallback и частичную недоступность email-уведомлений.

На странице также выполняется проверка `GET /api/health`. Поскольку frontend и
API имеют общий origin, отдельная CORS-настройка для встроенного лендинга не
требуется. CORS allowlist остается доступен для подключения внешнего frontend.

## Переменные окружения

Файл `.env` намеренно отсутствует в репозитории и добавлен в `.gitignore`:
он содержит пароли и API-ключи. Репозиторий предоставляет только безопасный
шаблон `.env.example`. После копирования шаблона необходимо указать собственные
учетные данные PostgreSQL и, при необходимости, собственные ключ OpenAI и
параметры SMTP.

Обязательные:

```dotenv
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5433
POSTGRESQL_USER=app_user
POSTGRESQL_PASSWORD=change_me
POSTGRESQL_DB=contact_service
```

AI:

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_MODEL=your-model
OPENAI_TIMEOUT_SECONDS=5
```

Рабочий `OPENAI_API_KEY` не публикуется в репозитории. Для проверки реального
AI-анализа необходимо указать собственный ключ OpenAI и доступную этому
API-проекту модель. Если ключ или модель отсутствуют, недействительны либо
провайдер недоступен, применяется AI fallback, а обращение продолжает
обрабатываться.

SMTP:

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=user@example.com
SMTP_PASSWORD=app_password
SMTP_SENDER_EMAIL=user@example.com
SMTP_OWNER_EMAIL=owner@example.com
SMTP_START_TLS=true
SMTP_USE_TLS=false
SMTP_TIMEOUT_SECONDS=10
```

SMTP-пароль также не публикуется. Для проверки реальной доставки необходимо
указать собственные SMTP credentials. При отсутствии SMTP-конфигурации
обращение сохраняется, а статусы почтовых уведомлений возвращаются как
`failed`.

Для STARTTLS обычно используется порт `587`. Для implicit TLS обычно
используется порт `465` с `SMTP_USE_TLS=true` и `SMTP_START_TLS=false`.
Обычный пароль почтового аккаунта не следует использовать, если провайдер
поддерживает отдельные пароли приложений.

Для безопасной локальной демонстрации можно использовать
[Mailtrap Email Sandbox](https://mailtrap.io/email-sandbox/). Создайте sandbox,
откройте его SMTP settings и перенесите выданные именно вашему sandbox значения
host, port, username и password в `.env`. Sandbox перехватывает письма и не
доставляет их реальным адресатам.

CORS и rate limit:

```dotenv
CORS_ORIGINS=["http://localhost:3000"]
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=900
TRUST_PROXY_HEADERS=false
```

`TRUST_PROXY_HEADERS=true` разрешается только при запуске за доверенным reverse
proxy, например на хостинге. Иначе клиент сможет подменить `X-Forwarded-For`.

## API

### `POST /api/contact`

```json
{
  "name": "Иван",
  "phone": "+7 (999) 123-45-67",
  "email": "ivan@example.com",
  "comment": "Нужна консультация по разработке backend-сервиса"
}
```

```bash
curl -X POST http://127.0.0.1:8000/api/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Иван","phone":"+7 (999) 123-45-67","email":"ivan@example.com","comment":"Нужна консультация по разработке backend-сервиса"}'
```

Успешный ответ — `201 Created`:

```json
{
  "id": "b59d125e-10fa-45b0-b355-aa6c1dc88b70",
  "status": "accepted",
  "ai_status": "fallback",
  "owner_email_status": "failed",
  "user_email_status": "failed"
}
```

Статусы fallback/failed означают, что внешняя интеграция недоступна, но
обращение уже сохранено.

### `GET /api/health`

Успешный ответ — `200 OK`:

```json
{
  "status": "healthy",
  "database": "up"
}
```

При недоступной БД возвращается `503 Service Unavailable`.

### `GET /api/metrics`

Возвращает агрегированную статистику без персональных данных:

```json
{
  "total_contacts": 3,
  "ai": {"completed": 0, "fallback": 3},
  "owner_email": {"pending": 0, "sent": 0, "failed": 3},
  "user_email": {"pending": 0, "sent": 0, "failed": 3},
  "categories": {"other": 3}
}
```

`METRICS_API_KEY` — внутренний секрет приложения, а не ключ OpenAI или
почтового провайдера. Владелец сервиса самостоятельно генерирует случайное
значение и сохраняет его в `.env`, например:

```env
METRICS_API_KEY=replace_with_a_long_random_value
```

Если `METRICS_API_KEY` задан, endpoint требует передать точно такое же значение
в HTTP-заголовке:

```text
X-Metrics-API-Key: replace_with_a_long_random_value
```

В Swagger значение вводится в поле `X-Metrics-API-Key` у запроса
`GET /api/metrics`. При неверном или отсутствующем ключе API возвращает
`403 Forbidden`. Если переменная `METRICS_API_KEY` не настроена или оставлена
пустой, агрегаты доступны публично. Endpoint выполняет два запроса к PostgreSQL:
один для условных счетчиков и один для группировки
категорий. Для небольшого административного endpoint это приемлемый компромисс.

### Ошибки

- `422` — ошибка валидации.
- `429` — превышение rate limit; присутствует `Retry-After`.
- `503` — операция с PostgreSQL недоступна.
- `500` — непредвиденная ошибка.

Каждый ответ содержит заголовок `X-Request-ID`. В публичные ошибки не попадают
SQL, traceback, credentials или пользовательские данные.

## AI-интеграция

В OpenAI передается только комментарий — имя, телефон и email не отправляются.
Responses API возвращает структурированный Pydantic-результат:

- категория: `project`, `consultation`, `job_offer`, `support`, `spam`, `other`;
- тональность: `positive`, `neutral`, `negative`;
- краткое резюме на языке пользователя.

Промпт указывает считать комментарий недоверенными данными, не выполнять
инструкции внутри него, не добавлять отсутствующие факты и возвращать только
заданную структуру.

Fallback применяется при отсутствии конфигурации, timeout, ошибке API,
невалидном или пустом структурированном ответе:

```text
category = other
sentiment = neutral
summary = первые 500 символов нормализованного комментария
```

## Email

Письмо владельцу содержит контакты, исходный комментарий и AI-анализ. Пользователь
получает только шаблонное подтверждение без сгенерированных AI обещаний.

Оба письма отправляются независимо. Ошибка одного адресата не отменяет вторую
отправку и не откатывает сохраненное обращение.

## Хранение, rate limiting и логи

Обращения и статусы интеграций хранятся в PostgreSQL. Схема управляется Alembic.

Rate limiter хранит скользящее окно запросов в памяти процесса. Это достаточное
решение для одного worker тестового сервиса, но счетчики сбрасываются при
рестарте и не синхронизируются между replicas. Для горизонтального
масштабирования следует заменить backend rate limiter на Redis.

Логи пишутся как JSON одновременно в stdout и ротируемый файл `logs/app.log`.
Записываются request ID, HTTP method, path, status и duration. Тела запросов,
email, телефоны, комментарии и секреты не логируются. На Render локальный файл
является ephemeral, поэтому stdout должен собираться платформой.

## Принятые trade-offs

- Статусы хранятся как строки, а допустимые значения контролируются Pydantic и
  service layer. Это упрощает первую миграцию; развитие системы потребует
  `CHECK` constraints или SQLAlchemy Enum.
- Отдельный domain entity и Unit of Work не добавлялись для одного простого
  агрегата. В более крупной системе service не должен зависеть от ORM-модели.
- SMTP выполняется внутри запроса после сохранения данных. Для гарантированных
  повторов в production нужен transactional outbox и отдельный worker.
- Idempotency key не используется: для формы обратной связи это усложнило бы
  публичный контракт без достаточной пользы.

## Деплой

Сервис можно развернуть как Docker web service, а PostgreSQL — как managed
database. На хостинге необходимо:

1. Добавить обязательные PostgreSQL variables.
2. Добавить OpenAI/SMTP secrets при использовании интеграций.
3. Указать `CORS_ORIGINS` для реального frontend origin.
4. Установить `TRUST_PROXY_HEADERS=true` только за доверенным proxy.
5. Проверить `/api/health` после запуска.

Docker image запускает `alembic upgrade head`, затем Uvicorn на порту из
переменной `PORT`.

## Что сделано с помощью AI

AI использовался как инженерный помощник:

- обсуждение scope и архитектурных trade-offs;
- ревью SQLAlchemy async repository и FastAPI Dependency Injection;
- подготовка OpenAI structured output и fallback;
- генерация SMTP, logging, rate limiting и Docker boilerplate;
- реализация минимального frontend: HTML-разметка, адаптивные стили и
  JavaScript-интеграция с REST API;
- диагностика миграций, портов PostgreSQL и Swagger;
- подготовка документации.

Примеры использованных запросов:

```text
Составь план реализации backend-тестового задания с FastAPI, PostgreSQL и AI.
Проверь repository на корректность SQLAlchemy Async и границы транзакций.
Реализуй OpenAI structured output с graceful fallback.
Добавь request logging, обработку ошибок и rate limiting без Redis.
Добавь минимальный адаптивный frontend и подключи форму к POST /api/contact.
```

Результаты AI проверялись вручную: исправлялись границы слоев, lifecycle сессии,
HTTP-статусы, настройки TLS, обработка PII, миграции, Docker-конфигурация и
соответствие frontend фактическому формату API-ошибок.
