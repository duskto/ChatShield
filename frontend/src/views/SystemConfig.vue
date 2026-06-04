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
          <el-descriptions-item label="当前运行模型">{{ appStore.activeModel || "未启动" }}</el-descriptions-item>
          <el-descriptions-item label="运行中模型">{{ appStore.runningModels?.join("、") || "暂无" }}</el-descriptions-item>
          <el-descriptions-item label="可用模型">{{ appStore.models?.join("、") || "未获取到" }}</el-descriptions-item>
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
        <el-alert
          title="规则说明：数据库自定义规则会叠加在系统内置规则之上，对输入和输出同时生效。"
          type="info"
          :closable="false"
          show-icon
        />
        <div class="model-actions">
          <el-select v-model="selectedModel" class="model-select" placeholder="选择要启动的模型">
            <el-option
              v-for="model in appStore.models"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          <el-button
            type="primary"
            :loading="appStore.modelStarting"
            :disabled="!selectedModel"
            @click="startModel"
          >
            启动模型
          </el-button>
        </div>
        <el-button type="primary" plain @click="refreshStatus">刷新状态</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { ElAlert, ElButton, ElDescriptions, ElDescriptionsItem, ElMessage, ElOption, ElSelect } from "element-plus";

import { useAppStore } from "../store/app";

const appStore = useAppStore();
const selectedModel = ref("");

watch(
  () => [appStore.activeModel, appStore.defaultModel, appStore.models],
  () => {
    if (appStore.activeModel) {
      selectedModel.value = appStore.activeModel;
      return;
    }
    if (!selectedModel.value || !appStore.models.includes(selectedModel.value)) {
      selectedModel.value = appStore.defaultModel || appStore.models[0] || "";
    }
  },
  { immediate: true, deep: true },
);

function refreshStatus() {
  appStore.hydrate(true).catch(() => {});
}

async function startModel() {
  if (!selectedModel.value) {
    ElMessage.warning("请先选择一个模型");
    return;
  }

  try {
    await appStore.ensureModelStarted(selectedModel.value);
    ElMessage.success(`模型 ${selectedModel.value} 已启动`);
  } catch (error) {
    ElMessage.error(error.message);
  }
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

.model-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.model-select {
  min-width: 240px;
}
</style>
