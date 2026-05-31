<template>
  <div class="page-shell">
    <div>
      <h1 class="page-title">系统配置</h1>
      <p class="page-subtitle">展示当前后端启用的模型、安全策略和依赖状态。</p>
    </div>

    <div class="grid-two">
      <div class="page-card config-card">
        <div class="config-title">运行配置</div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="应用名称">{{ appStore.config?.app_name }}</el-descriptions-item>
          <el-descriptions-item label="环境">{{ appStore.config?.environment }}</el-descriptions-item>
          <el-descriptions-item label="Ollama URL">{{ appStore.config?.ollama_base_url }}</el-descriptions-item>
          <el-descriptions-item label="默认模型">{{ appStore.config?.ollama_model }}</el-descriptions-item>
          <el-descriptions-item label="审核提供商">{{ appStore.config?.moderation_provider }}</el-descriptions-item>
          <el-descriptions-item label="输入拦截阈值">{{ appStore.config?.input_block_threshold }}</el-descriptions-item>
          <el-descriptions-item label="输出拦截阈值">{{ appStore.config?.output_block_threshold }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="page-card config-card">
        <div class="config-title">依赖状态</div>
        <el-alert
          :title="`Ollama：${appStore.ollamaStatus?.message || '加载中'}`"
          :type="appStore.ollamaStatus?.available ? 'success' : 'error'"
          :closable="false"
          show-icon
        />
        <el-alert
          :title="`审核服务：${appStore.moderationStatus?.message || '加载中'}`"
          :type="appStore.moderationStatus?.available ? 'success' : 'warning'"
          :closable="false"
          show-icon
        />
        <el-button type="primary" plain @click="refreshStatus">刷新状态</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from "../store/app";

const appStore = useAppStore();

function refreshStatus() {
  appStore.hydrate().catch(() => {});
}
</script>

<style scoped>
.config-card {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.config-title {
  font-size: 20px;
  font-weight: 700;
}
</style>
