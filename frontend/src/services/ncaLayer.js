/**
 * NCALayer WebSocket client.
 * NCALayer 1.4: wss://127.0.0.1:13579 + legacy "createCMSSignatureFromBase64" API
 */

const TIMEOUT_MS = 300_000  // 5 min – time for user to find and interact with cert dialog

function parseLegacyResponse(resp) {
  // NCALayer 1.4 sends {"result":{"version":"1.4"}} immediately on connect — ignore it
  if (resp.result?.version && Object.keys(resp.result).length === 1) {
    console.log('[NCALayer] Got version greeting:', resp.result.version, '— waiting for sign response...')
    return null  // skip, wait for actual sign response
  }

  // NCALayer 1.4 legacy format: { code: "200", message: "...", responseObject: "BASE64_CMS" }
  if (resp.code === '200' && resp.responseObject) return { ok: true, cms: resp.responseObject }
  if (resp.code === 200 && resp.responseObject) return { ok: true, cms: resp.responseObject }
  if (resp.code) {
    const cancelled = /cancel|отмен/i.test(resp.message ?? '')
    return cancelled
      ? { ok: false, cancelled: true }
      : { ok: false, error: `[${resp.code}] ${resp.message || 'Ошибка'}` }
  }
  // JSON-RPC 2.0 format (NCALayer 1.5+)
  if (resp.result?.cms) return { ok: true, cms: resp.result.cms }
  if (resp.result?.responseObject) return { ok: true, cms: resp.result.responseObject }
  if (resp.error) {
    const msg = resp.error.message ?? ''
    return /cancel|отмен/i.test(msg)
      ? { ok: false, cancelled: true }
      : { ok: false, error: msg || `Код ошибки ${resp.error.code}` }
  }
  console.warn('[NCALayer] Unrecognised response format:', resp)
  return { ok: false, error: `Неизвестный формат ответа: ${JSON.stringify(resp)}` }
}

export function signWithNcaLayer(data) {
  const dataBase64 = btoa(unescape(encodeURIComponent(data)))

  return new Promise((resolve, reject) => {
    let ws
    let timer
    let settled = false

    function cleanup() {
      clearTimeout(timer)
      try { ws?.close() } catch (_) {}
    }

    function settle(fn, value) {
      if (settled) return
      settled = true
      cleanup()
      fn(value)
    }

    console.log('[NCALayer] Connecting to wss://127.0.0.1:13579 ...')
    try {
      ws = new WebSocket('wss://127.0.0.1:13579')
    } catch (e) {
      reject(new Error('Не удалось создать WebSocket: ' + e.message))
      return
    }

    ws.onerror = (e) => {
      console.error('[NCALayer] Connection error (onerror):', e)
      settle(reject, new Error(
        'Не удалось подключиться к NCALayer по wss://127.0.0.1:13579\n\n' +
        'Убедитесь:\n' +
        '1. NCALayer запущен (иконка в трее)\n' +
        '2. В браузере открыта вкладка https://127.0.0.1:13579 без предупреждений безопасности'
      ))
    }

    ws.onopen = () => {
      console.log('[NCALayer] Connected! Sending sign request...')

      ws.onerror = (e) => {
        console.error('[NCALayer] Post-connect error:', e)
        settle(reject, new Error('Ошибка соединения с NCALayer после подключения.'))
      }

      ws.onclose = (e) => {
        console.warn('[NCALayer] Connection closed:', e.code, e.reason, 'wasClean:', e.wasClean)
        if (!settled) {
          settle(reject, new Error(
            'NCALayer закрыл соединение без ответа (code ' + e.code + ').\n\n' +
            'Возможные причины:\n' +
            '• Диалог выбора сертификата открылся ПОЗАДИ браузера — найдите его на панели задач Windows и кликните\n' +
            '• Введён неверный пароль от файла .p12\n' +
            '• Файл сертификата повреждён'
          ))
        }
      }

      const request = {
        module: 'kz.gov.pki.knca.commonUtils',
        method: 'createCMSSignatureFromBase64',
        args: ['PKCS12', 'SIGNATURE', dataBase64, true],
      }
      console.log('[NCALayer] Sending:', JSON.stringify(request).substring(0, 120) + '...')
      ws.send(JSON.stringify(request))

      timer = setTimeout(() => {
        settle(reject, new Error('Время ожидания ответа от NCALayer истекло (5 минут).'))
      }, TIMEOUT_MS)
    }

    ws.onmessage = (event) => {
      console.log('[NCALayer] Received message:', event.data.substring(0, 200))
      let resp
      try { resp = JSON.parse(event.data) }
      catch { settle(reject, new Error('Некорректный JSON от NCALayer: ' + event.data.substring(0, 100))); return }

      const parsed = parseLegacyResponse(resp)
      if (parsed === null) return  // intermediate message (e.g. version greeting) — wait for next
      if (parsed.ok) {
        console.log('[NCALayer] Signing successful! CMS length:', parsed.cms?.length)
        settle(resolve, parsed.cms)
      } else if (parsed.cancelled) {
        settle(reject, new Error('Подписание отменено пользователем.'))
      } else {
        settle(reject, new Error('NCALayer: ' + parsed.error))
      }
    }
  })
}
