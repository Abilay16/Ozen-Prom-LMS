// БиОТ для ИТР выдаётся на 3 года (рабочим — на 1 год) и оформляется
// сертификатом, а не удостоверением. Определяем по сроку: от 30 месяцев.
export function isBiotItrCertificate(cert) {
  if (cert?.training_type?.code !== 'biot' || !cert.issued_date || !cert.valid_until) return false
  const from = new Date(cert.issued_date + 'T00:00:00')
  const to = new Date(cert.valid_until + 'T00:00:00')
  return (to.getFullYear() - from.getFullYear()) * 12 + (to.getMonth() - from.getMonth()) >= 30
}
