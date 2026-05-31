<template>
  <div class="message-row" :class="role">
    <div class="message-role">{{ role === "user" ? "用户" : "模型" }}</div>
    <div class="message-bubble">{{ content }}</div>
  </div>
</template>

<script setup>
defineProps({
  role: {
    type: String,
    required: true,
  },
  content: {
    type: String,
    required: true,
  },
});
</script>

<style scoped>
.message-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.message-row.user {
  align-items: flex-end;
}

.message-role {
  font-size: 12px;
  color: var(--muted);
}

.message-bubble {
  max-width: 85%;
  padding: 14px 16px;
  border-radius: 18px;
  background: var(--panel-strong);
  border: 1px solid var(--line);
  white-space: pre-wrap;
  line-height: 1.7;
}

.message-row.user .message-bubble {
  background: linear-gradient(135deg, #145f59, #2e847d);
  color: white;
}
</style>

