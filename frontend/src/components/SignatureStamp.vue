<template>
  <div class="signature-stamp" :class="compact ? 'compact' : ''">
    <div class="stamp-inner">
      <div class="stamp-title">ДОКУМЕНТ ПОДПИСАН<br/>ЭЛЕКТРОННОЙ ПОДПИСЬЮ</div>
      <div class="stamp-divider"></div>
      <div class="stamp-row">
        <span class="stamp-label">Серийный №:</span>
        <span class="stamp-value serial">{{ serial }}</span>
      </div>
      <div class="stamp-row">
        <span class="stamp-label">Владелец:</span>
        <span class="stamp-value">{{ owner }}</span>
      </div>
      <div class="stamp-row">
        <span class="stamp-label">Действителен:</span>
        <span class="stamp-value">{{ formatDate(validFrom) }} — {{ formatDate(validTo) }}</span>
      </div>
      <div class="stamp-row">
        <span class="stamp-label">Подписано:</span>
        <span class="stamp-value">{{ formatDateTime(signedAt) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  serial:    { type: String, default: '' },
  owner:     { type: String, default: '' },
  validFrom: { type: String, default: null },
  validTo:   { type: String, default: null },
  signedAt:  { type: String, default: null },
  compact:   { type: Boolean, default: false },
})

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatDateTime(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<style scoped>
.signature-stamp {
  display: inline-block;
  border: 2px solid #1a7a1a;
  border-radius: 4px;
  padding: 8px 12px;
  background: rgba(26, 122, 26, 0.04);
  font-family: monospace;
  font-size: 11px;
  color: #1a5a1a;
  max-width: 340px;
}
.compact {
  font-size: 9px;
  padding: 5px 8px;
  max-width: 260px;
}
.stamp-inner {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.stamp-title {
  font-weight: bold;
  font-size: 10px;
  letter-spacing: 0.5px;
  text-align: center;
  line-height: 1.3;
  text-transform: uppercase;
}
.compact .stamp-title {
  font-size: 8px;
}
.stamp-divider {
  border-top: 1px solid #1a7a1a;
  margin: 3px 0;
}
.stamp-row {
  display: flex;
  gap: 4px;
  align-items: flex-start;
}
.stamp-label {
  color: #4a8a4a;
  white-space: nowrap;
  flex-shrink: 0;
}
.stamp-value {
  color: #1a3a1a;
  word-break: break-all;
}
.stamp-value.serial {
  font-size: 10px;
  letter-spacing: 0.5px;
}
</style>
