<template>
  <div class="page-card detection-card" :class="`level-${detection.risk_level}`">
    <div class="detection-head">
      <div>
        <div class="detection-stage">{{ stageLabel }}</div>
        <div class="detection-level">{{ detection.risk_level.toUpperCase() }}</div>
      </div>
      <RiskTag :label="blockedLabel" :level="detection.risk_level" />
    </div>
    <div class="detection-grid">
      <div>
        <div class="label">处理动作</div>
        <div class="value">{{ detection.action }}</div>
      </div>
      <div>
        <div class="label">审核来源</div>
        <div class="value">{{ sourceText }}</div>
      </div>
      <div>
        <div class="label">识别意图</div>
        <div class="value">{{ intentText }}</div>
      </div>
      <div>
        <div class="label">识别场景</div>
        <div class="value">{{ scenarioText }}</div>
      </div>
      <div>
        <div class="label">可执行性</div>
        <div class="value">{{ actionabilityText }}</div>
      </div>
    </div>
    <div>
      <div class="label">风险类型</div>
      <div class="tag-row">
        <RiskTag
          v-for="riskType in normalizedTypes"
          :key="riskType"
          :label="riskType"
          :level="detection.risk_level"
        />
      </div>
    </div>
    <div>
      <div class="label">判断原因</div>
      <div class="reason">{{ detection.reason }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

import RiskTag from "./RiskTag.vue";

const props = defineProps({
  stage: {
    type: String,
    required: true,
  },
  detection: {
    type: Object,
    required: true,
  },
});

const stageLabel = computed(() => (props.stage === "input" ? "输入检测" : "输出检测"));
const blockedLabel = computed(() => (props.detection.action === "block" ? "已拦截" : "已放行"));
const sourceText = computed(() => props.detection.sources?.join(" + ") || props.detection.provider || "rule");
const normalizedTypes = computed(() => props.detection.risk_types?.length ? props.detection.risk_types : ["normal"]);
const intentLabels = {
  discuss: "讨论/科普",
  analyze: "分析",
  translate: "翻译/转述",
  audit: "审计",
  generate: "生成",
  execute: "执行",
  bypass: "绕过",
  unknown: "未知",
};
const scenarioLabels = {
  general: "一般场景",
  security_explanation: "安全解释",
  security_analysis: "安全分析",
  content_transformation: "内容转换",
  log_analysis: "日志分析",
  code_review: "代码审查",
  red_team_request: "红队请求",
  malicious_generation: "恶意生成",
  malicious_execution: "恶意执行",
  data_exfiltration_request: "数据外流请求",
  risk_mention: "风险提及",
};
const actionabilityLabels = {
  low: "低",
  medium: "中",
  high: "高",
};
const intentText = computed(() => intentLabels[props.detection.intent] || props.detection.intent || "未知");
const scenarioText = computed(() => scenarioLabels[props.detection.scenario] || props.detection.scenario || "一般场景");
const actionabilityText = computed(
  () => actionabilityLabels[props.detection.actionability] || props.detection.actionability || "低",
);
</script>

<style scoped>
.detection-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detection-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.detection-stage {
  color: var(--muted);
  font-size: 13px;
}

.detection-level {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 800;
}

.detection-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.label {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 8px;
}

.value,
.reason {
  font-weight: 600;
  line-height: 1.6;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.level-medium {
  border-color: rgba(208, 138, 30, 0.3);
}

.level-high,
.level-critical {
  border-color: rgba(181, 63, 43, 0.3);
}

@media (max-width: 900px) {
  .detection-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .detection-grid {
    grid-template-columns: 1fr;
  }
}
</style>
