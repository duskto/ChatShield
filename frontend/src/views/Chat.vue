<template>
  <div class="page-shell">
    <div class="chat-hero">
      <div>
        <h1 class="page-title">安全聊天测试台</h1>
        <p class="page-subtitle">用户输入和模型输出都会经过规则检测与语义审核。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="form.model" class="model-select" placeholder="选择模型">
          <el-option :label="defaultModel" :value="defaultModel" />
        </el-select>
        <el-button plain @click="clearMessages">清空记录</el-button>
      </div>
    </div>

    <div class="grid-two">
      <div class="page-card chat-panel">
        <div class="chat-scroll">
          <ChatMessage
            v-for="(item, index) in messages"
            :key="`${item.role}-${index}`"
            :role="item.role"
            :content="item.content"
          />
        </div>
        <div class="composer">
          <el-input
            v-model="form.message"
            type="textarea"
            :rows="4"
            maxlength="8000"
            resize="none"
            placeholder="输入消息，例如：你好，介绍一下你自己"
          />
          <div class="composer-foot">
            <span class="composer-tip">高风险输入会在调用模型前直接拦截。</span>
            <el-button type="primary" :loading="loading" @click="submitChat">发送</el-button>
          </div>
        </div>
      </div>

      <div class="page-shell">
        <DetectionCard v-if="latestInputDetection" stage="input" :detection="latestInputDetection" />
        <DetectionCard v-if="latestOutputDetection" stage="output" :detection="latestOutputDetection" />
        <el-empty v-if="!latestInputDetection && !latestOutputDetection" description="发送一条消息后查看检测结果" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { sendChatMessage } from "../api/chat";
import ChatMessage from "../components/ChatMessage.vue";
import DetectionCard from "../components/DetectionCard.vue";
import { useAppStore } from "../store/app";

const appStore = useAppStore();
const loading = ref(false);
const messages = ref([
  {
    role: "assistant",
    content: "这里是 ChatShield 演示界面。你可以测试正常聊天、隐私信息和高风险输入拦截。",
  },
]);
const latestInputDetection = ref(null);
const latestOutputDetection = ref(null);

const defaultModel = computed(() => appStore.config?.ollama_model || "qwen2.5:3b");
const form = reactive({
  message: "",
  model: defaultModel.value,
});

async function submitChat() {
  if (!form.message.trim()) {
    ElMessage.warning("请输入消息");
    return;
  }

  loading.value = true;
  messages.value.push({ role: "user", content: form.message.trim() });

  try {
    const data = await sendChatMessage({
      message: form.message.trim(),
      model: form.model || defaultModel.value,
    });
    latestInputDetection.value = data.input_detection;
    latestOutputDetection.value = data.output_detection;
    messages.value.push({ role: "assistant", content: data.reply });
    form.message = "";
  } catch (error) {
    ElMessage.error(error.message);
    messages.value.push({ role: "assistant", content: `请求失败：${error.message}` });
  } finally {
    loading.value = false;
  }
}

function clearMessages() {
  messages.value = [];
  latestInputDetection.value = null;
  latestOutputDetection.value = null;
}
</script>

<style scoped>
.chat-hero {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-end;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.model-select {
  min-width: 200px;
}

.chat-panel {
  min-height: 720px;
  padding: 22px;
  display: grid;
  grid-template-rows: 1fr auto;
  gap: 18px;
}

.chat-scroll {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: auto;
  padding-right: 4px;
}

.composer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.composer-foot {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.composer-tip {
  color: var(--muted);
  font-size: 13px;
}

@media (max-width: 1024px) {
  .chat-hero,
  .composer-foot {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

