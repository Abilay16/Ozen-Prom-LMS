// Роль текущего админ-аккаунта. Флаги пишутся в localStorage при входе,
// а вход делает полную перезагрузку страницы — поэтому читать один раз безопасно.
//
//  isCommission — член комиссии: видит протоколы и подписывает, ничего не создаёт.
//  isOrgViewer  — наблюдатель организации: только просмотр своей организации.
//  canEdit      — может создавать/изменять/удалять (обычный и суперадмин).
export function useRole() {
  const isCommission = localStorage.getItem('is_commission') === '1'
  const isOrgViewer = localStorage.getItem('is_org_viewer') === '1'
  return {
    isCommission,
    isOrgViewer,
    canEdit: !isCommission && !isOrgViewer,
  }
}
