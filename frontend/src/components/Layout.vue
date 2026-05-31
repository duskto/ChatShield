<template>
  <div class="layout-shell">
    <aside class="side-nav page-card">
      <div class="brand-block">
        <div class="brand-mark">CS</div>
        <div>
          <div class="brand-name">{{ appStore.title }}</div>
          <div class="brand-desc">AI Chat 内容安全检测与审计</div>
        </div>
      </div>
      <el-menu :default-active="$route.path" router class="menu-panel">
        <el-menu-item index="/chat">Chat 对话测试</el-menu-item>
        <el-menu-item index="/dashboard">Dashboard 风险看板</el-menu-item>
        <el-menu-item index="/logs">Audit Logs 审计日志</el-menu-item>
        <el-menu-item index="/config">System Config 系统配置</el-menu-item>
      </el-menu>
    </aside>
    <main class="main-shell">
      <header class="topbar page-card">
        <div>
          <div class="topbar-title">{{ currentTitle }}</div>
          <div class="topbar-subtitle">默认模型：{{ appStore.config?.ollama_model || "加载中" }}</div>
        </div>
        <div class="status-row">
          <div class="status-pill" :class="{ online: appStore.ollamaStatus?.available }">
            Ollama {{ appStore.ollamaStatus?.available ? "在线" : "离线" }}
          </div>
          <div class="status-pill" :class="{ online: appStore.moderationStatus?.available }">
            审核 {{ appStore.moderationStatus?.available ? "在线" : "降级" }}
          </div>
        </div>
      </header>
      <section class="content-shell">
        <router-view />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";

import { useAppStore } from "../store/app";

const route = useRoute();
const appStore = useAppStore();

const currentTitle = computed(() => route.meta.title || appStore.title);

onMounted(() => {
  appStore.hydrate().catch(() => {});
});
</script>

<style scoped>
.layout-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  min-height: 100vh;
  padding: 18px;
  gap: 18px;
}

.side-nav {
  padding: 22px 18px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.brand-block {
  display: flex;
  gap: 14px;
  align-items: center;
}

.brand-mark {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: linear-gradient(135deg, #145f59, #2e847d);
  color: white;
  font-weight: 800;
  letter-spacing: 1px;
}

.brand-name {
  font-size: 22px;
  font-weight: 800;
}

.brand-desc {
  margin-top: 4px;
  color: var(--muted);
  font-size: 13px;
}

.menu-panel {
  border-right: none;
  background: transparent;
}

.main-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.topbar {
  min-height: 92px;
  padding: 18px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topbar-title {
  font-size: 28px;
  font-weight: 800;
}

.topbar-subtitle {
  margin-top: 6px;
  color: var(--muted);
}

.status-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.status-pill {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(181, 63, 43, 0.12);
  color: var(--danger);
  font-weight: 600;
}

.status-pill.online {
  background: rgba(47, 125, 73, 0.12);
  color: var(--success);
}

.content-shell {
  min-height: 0;
}

@media (max-width: 960px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }
}
</style>

