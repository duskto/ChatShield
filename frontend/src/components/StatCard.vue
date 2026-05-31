<template>
  <div class="page-card stat-card">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value">{{ value }}</div>
    <div class="stat-note">{{ note }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  note: {
    type: String,
    default: "",
  },
});
</script>

<style scoped>
.stat-card {
  padding: 22px;
}

.stat-label {
  color: var(--muted);
  font-size: 13px;
}

.stat-value {
  margin-top: 12px;
  font-size: 34px;
  font-weight: 800;
}

.stat-note {
  margin-top: 8px;
  color: var(--muted);
  font-size: 13px;
}
</style>

