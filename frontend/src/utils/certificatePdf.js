// Настоящее скачивание сертификата БиОТ ИТР файлом PDF (раньше «Скачать PDF»
// открывало диалог печати). Лист снимается в картинку высокого разрешения
// и кладётся на альбомный A4 — вид один в один как на экране, со штампом ЭЦП.
// Библиотеки тяжёлые, поэтому грузятся только при нажатии.

const PAGE_W_PT = 842.25
const PAGE_H_PT = 595.5

export async function downloadBiotCertificatePdf(fileName) {
  const node = document.querySelector('.biot-cert')
  if (!node) throw new Error('Сертификат ещё не загрузился')

  const [{ toJpeg }, { jsPDF }] = await Promise.all([import('html-to-image'), import('jspdf')])
  await document.fonts?.ready

  const widthPx = PAGE_W_PT * 4 / 3
  const heightPx = PAGE_H_PT * 4 / 3
  // На экране лист уменьшен transform'ом — снимаем без масштаба.
  const opts = {
    width: widthPx,
    height: heightPx,
    pixelRatio: 3,
    quality: 0.92,
    backgroundColor: '#ffffff',
    style: { transform: 'none', position: 'static' },
  }
  // Первый снимок иногда без шрифтов/картинок (Safari) — второй уже полный.
  await toJpeg(node, { ...opts, pixelRatio: 1 })
  const img = await toJpeg(node, opts)

  const pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: [PAGE_W_PT, PAGE_H_PT], compress: true })
  pdf.addImage(img, 'JPEG', 0, 0, PAGE_W_PT, PAGE_H_PT)
  pdf.save(`${fileName}.pdf`)
}
