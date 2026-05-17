# Настройка ЭЦП (NCALayer) для LMS

## Что нужно для работы

| Компонент | Описание |
|---|---|
| NCALayer 1.4 | Установлен по адресу `C:\Users\<USER>\AppData\Roaming\NCALayer\NCALayer.exe` |
| Файл ключа ЭЦП | `.p12` файл, например `D:\ecp\GOST512_0f15581f1cbda1567ff8b09eb351e8ea9cb2b290.p12` |
| Сертификаты ЦА | Корневой и промежуточный сертификаты НЦУО (НУЦ РК) |

---

## Шаг 1 — Установить сертификаты удостоверяющего центра НУЦ РК

Без этого браузер будет блокировать подключение к `wss://127.0.0.1:13579`.

Скачать сертификаты: **https://pki.gov.kz/ru/ncalayer/**  
(раздел «Корневые сертификаты» → скачать `root.cer` и `issuing.cer`)

Установить через PowerShell **от имени пользователя** (не администратора):

```powershell
# Корневой CA (Kazakhstan Root CA)
Import-Certificate -FilePath "C:\путь\к\root.cer" -CertStoreLocation Cert:\CurrentUser\Root

# Промежуточный CA (НУЦРК / НУЦ РК)
Import-Certificate -FilePath "C:\путь\к\issuing.cer" -CertStoreLocation Cert:\CurrentUser\CA
```

Также нужно добавить сертификат самого NCALayer (127.0.0.1):

```powershell
# Скачать сертификат NCALayer с работающего сервера
$tcpClient = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 13579)
$sslStream = New-Object System.Net.Security.SslStream($tcpClient.GetStream(), $false, ({ $true }))
$sslStream.AuthenticateAsClient("127.0.0.1")
$cert = $sslStream.RemoteCertificate
$bytes = $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
[System.IO.File]::WriteAllBytes("C:\ncalayer_cert.cer", $bytes)
$sslStream.Dispose(); $tcpClient.Dispose()

# Установить в доверенные корневые
Import-Certificate -FilePath "C:\ncalayer_cert.cer" -CertStoreLocation Cert:\CurrentUser\Root
```

### Проверка установки

```powershell
# Должен завершиться без ошибки "not trusted"
$tc = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 13579)
$ssl = New-Object System.Net.Security.SslStream($tc.GetStream(), $false)
$ssl.AuthenticateAsClient("127.0.0.1")
Write-Host "SSL OK — сертификат доверен"
$ssl.Dispose(); $tc.Dispose()
```

### Перезапустить браузер

После установки сертификатов **полностью закрыть и снова открыть** браузер.  
Проверить: открыть `https://127.0.0.1:13579` — должен показать «Not Found» **с замком** (без предупреждения безопасности).

---

## Шаг 2 — Запустить NCALayer

- Запустить `NCALayer.exe`
- Иконка должна появиться в системном трее (правый нижний угол)
- NCALayer слушает на порту **13579** по протоколу **WSS** (TLS)

> **Важно:** NCALayer 1.4 работает **только** через `wss://` (TLS).  
> Соединение по `ws://` (без TLS) NCALayer отклоняет.

---

## Шаг 3 — Как работает подпись в коде

Файл: `frontend/src/services/ncaLayer.js`

### Протокол обмена

1. **Браузер** устанавливает WebSocket соединение с `wss://127.0.0.1:13579`
2. **NCALayer** сразу отправляет приветственное сообщение: `{"result":{"version":"1.4"}}`  
   → Это нужно **игнорировать** (не считать за ответ на запрос)
3. **Браузер** отправляет JSON-запрос:
   ```json
   {
     "module": "kz.gov.pki.knca.commonUtils",
     "method": "createCMSSignatureFromBase64",
     "args": ["PKCS12", "SIGNATURE", "<base64 данных>", true]
   }
   ```
4. **NCALayer** открывает диалог выбора `.p12` файла  
   → Пользователь выбирает файл и вводит пароль
5. **NCALayer** возвращает ответ:
   ```json
   { "code": "200", "responseObject": "<base64 CMS-подписи>" }
   ```

### Аргументы `createCMSSignatureFromBase64` в NCALayer 1.4

| Позиция | Значение | Описание |
|---|---|---|
| `args[0]` | `"PKCS12"` | Тип хранилища ключей |
| `args[1]` | `"SIGNATURE"` | Тип ключа (подпись, не аутентификация) |
| `args[2]` | `"<base64>"` | Подписываемые данные в Base64 |
| `args[3]` | `true` | `attached` — вложить данные в CMS-пакет |

> **Отличие от старых версий (до 1.4):**  
> Старая сигнатура: `(storageName, keyType, inputType, inputData, encapsulate, digested)` — 6 аргументов  
> Новая сигнатура: `(storageName, keyType, base64_data, attached)` — **4 аргумента**  
> Убраны: параметр `inputType` (всегда `"BASE64"`) и `digested` (boolean)

### Кодирование данных перед подписью

```javascript
// Корректное UTF-8 → Base64 для кириллицы и спецсимволов
const dataBase64 = btoa(unescape(encodeURIComponent(data)))
```

---

## Типичные ошибки и решения

### `NoSuchMethodException createCMSSignatureFromBase64`
**Причина:** передано неверное количество аргументов.  
**Решение:** убедиться что передаётся ровно 4 аргумента (см. таблицу выше).

### Браузер блокирует `wss://` соединение
**Причина:** сертификат NCALayer не добавлен в доверенные.  
**Решение:** выполнить Шаг 1 и перезапустить браузер.

### NCALayer закрывает соединение без ответа
**Причина:** диалог выбора сертификата открылся **позади** окна браузера.  
**Решение:** найти окно NCALayer на панели задач Windows и нажать на него.

### `{"result":{"version":"1.4"}}` вместо подписи
**Причина:** это приветственное сообщение — не ошибка.  
**Решение:** дождаться следующего сообщения (реальный ответ). Код уже обрабатывает это корректно.

### Ошибка `code: "500"`, message содержит имя метода
**Причина:** неверное имя метода или количество аргументов в запросе.  
**Решение:** проверить название метода и аргументы по таблице выше.

---

## Структура хранилища NCALayer

```
C:\Users\<USER>\AppData\Roaming\NCALayer\
├── NCALayer.exe
├── settings.json          — настройки (последний открытый .p12 и др.)
├── jre\                   — встроенная JRE
└── ncalayer-cache\
    ├── bundle5\           — CommonUtils (kz.gov.pki.knca.commonUtils)
    │   └── bundle.jar     → CommonUtils.class, NCALayerCommonActivator.class
    ├── bundle7\           — WebSocket сервер
    ├── bundle9\           — Applet (подпись через .p12 / токен)
    │   └── bundle.jar     → MainApplet.class, Applet.class
    └── bundle10\          — API layer / CommonInvoker
```

**bundle5** — отвечает за метод `createCMSSignatureFromBase64`  
**bundle9** — реализует низкоуровневую CMS-подпись через JCE  
**bundle7** — WebSocket сервер, принимает JSON `{ module, method, args }`

---

## Быстрая проверка работоспособности

1. NCALayer запущен (иконка в трее)
2. Открыть `https://127.0.0.1:13579` — замок есть, «Not Found» (нормально)
3. Зайти в LMS, открыть протокол со статусом «Ожидает подписи»
4. Нажать «Подписать» — должен появиться диалог выбора `.p12` файла
5. Выбрать файл ключа, ввести пароль — появится штамп ЭЦП в разделе «Состав комиссии»
