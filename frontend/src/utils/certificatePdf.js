// Настоящее скачивание документов файлом PDF (раньше «Скачать PDF»
// открывало диалог печати). Лист снимается в картинку высокого разрешения
// и кладётся на страницу нужного размера — вид один в один как на экране.
// Библиотеки тяжёлые, поэтому грузятся только при нажатии.

async function snapshot(node, widthPx, heightPx, pixelRatio) {
  const { toJpeg } = await import('html-to-image')
  await document.fonts?.ready
  // На экране лист уменьшен transform'ом — снимаем без масштаба.
  const opts = {
    width: widthPx,
    height: heightPx,
    pixelRatio,
    quality: 0.93,
    backgroundColor: '#ffffff',
    style: { transform: 'none', position: 'static' },
  }
  // Первый снимок иногда без шрифтов/картинок (Safari) — второй уже полный.
  await toJpeg(node, { ...opts, pixelRatio: 1 })
  return toJpeg(node, opts)
}

async function savePdf(img, widthUnits, heightUnits, unit, fileName) {
  const { jsPDF } = await import('jspdf')
  const pdf = new jsPDF({ orientation: 'landscape', unit, format: [widthUnits, heightUnits], compress: true })
  pdf.addImage(img, 'JPEG', 0, 0, widthUnits, heightUnits)
  pdf.save(`${fileName}.pdf`)
}

// ── Сертификат БиОТ ИТР: альбомный A4 ───────────────────────────────────────
const A4_W_PT = 842.25
const A4_H_PT = 595.5

export async function downloadBiotCertificatePdf(fileName) {
  const node = document.querySelector('.biot-cert')
  if (!node) throw new Error('Сертификат ещё не загрузился')
  const img = await snapshot(node, A4_W_PT * 4 / 3, A4_H_PT * 4 / 3, 3)
  await savePdf(img, A4_W_PT, A4_H_PT, 'pt', fileName)
}

// ── Карта работника: 85,6 × 54 мм (CR80) ─────────────────────────────────────
const CARD_W_MM = 85.6
const CARD_H_MM = 54

export function workerCardImage(node, widthPx, heightPx) {
  // Макет уже 1579 px в ширину (~470 dpi на карте) — увеличивать не нужно.
  return snapshot(node, widthPx, heightPx, 1)
}

export async function downloadWorkerCardPdf(img, fileName) {
  await savePdf(img, CARD_W_MM, CARD_H_MM, 'mm', fileName)
}

// Печать без всплывающего окна (его блокируют браузеры после await):
// скрытый iframe с одной картинкой на листе размера карты.
export function printWorkerCard(img) {
  const iframe = document.createElement('iframe')
  iframe.setAttribute('aria-hidden', 'true')
  iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;'
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  doc.open()
  doc.write(`<!doctype html><html><head><meta charset="utf-8"><title>Карта работника</title><style>
    @page { size: ${CARD_W_MM}mm ${CARD_H_MM}mm; margin: 0; }
    html, body { margin: 0; padding: 0; }
    img { display: block; width: ${CARD_W_MM}mm; height: ${CARD_H_MM}mm; }
  </style></head><body><img src="${img}" alt=""></body></html>`)
  doc.close()
  const go = () => {
    iframe.contentWindow.focus()
    iframe.contentWindow.print()
    setTimeout(() => iframe.remove(), 60_000)
  }
  const pic = doc.querySelector('img')
  if (pic.complete) go()
  else pic.onload = go
}
