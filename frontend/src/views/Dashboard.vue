<template>
  <div class="page-shell">
    <div>
      <h1 class="page-title">风险看板</h1>
      <p class="page-subtitle">聚合审计日志中的风险等级、风险类型和拦截趋势。</p>
    </div>

    <div class="grid-three">
      <StatCard label="总检测次数" :value="stats.total_requests" note="所有进入网关的聊天请求" />
      <StatCard label="输入拦截次数" :value="stats.input_blocked" note="在调用模型前被阻断" />
      <StatCard label="输出拦截次数" :value="stats.output_blocked" note="模型回复已替换为安全提示" />
    </div>

    <div class="grid-two">
      <div class="page-card chart-panel">
        <div class="chart-title">风险等级分布</div>
        <div ref="riskLevelChartRef" class="chart-box"></div>
      </div>
      <div class="page-card chart-panel">
        <div class="chart-title">每日请求趋势</div>
        <div ref="trendChartRef" class="chart-box"></div>
      </div>
    </div>

    <div class="grid-two">
      <div class="page-card chart-panel">
        <div class="chart-title">风险类型分布</div>
        <div ref="riskTypeChartRef" class="chart-box"></div>
      </div>
      <div class="page-card table-panel">
        <div class="chart-title">最近高风险日志</div>
        <el-table :data="stats.recent_high_risk_logs" height="320">
          <el-table-column prop="created_at" label="时间" min-width="180" />
          <el-table-column prop="risk_level" label="等级" width="100" />
          <el-table-column prop="blocked_stage" label="阶段" width="100" />
          <el-table-column prop="reason" label="原因" min-width="220" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { BarChart, LineChart, PieChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { init, use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { ElTable, ElTableColumn } from "element-plus";
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";

import { fetchDashboardStats } from "../api/dashboard";
import StatCard from "../components/StatCard.vue";

use([TooltipComponent, GridComponent, PieChart, BarChart, LineChart, CanvasRenderer]);

const stats = reactive({
  total_requests: 0,
  input_blocked: 0,
  output_blocked: 0,
  allowed: 0,
  api_moderation_calls: 0,
  risk_level_distribution: {},
  risk_type_distribution: {},
  daily_requests: [],
  recent_high_risk_logs: [],
});

const riskLevelChartRef = ref(null);
const riskTypeChartRef = ref(null);
const trendChartRef = ref(null);
let riskLevelChart;
let riskTypeChart;
let trendChart;

function renderCharts() {
  riskLevelChart ??= init(riskLevelChartRef.value);
  riskTypeChart ??= init(riskTypeChartRef.value);
  trendChart ??= init(trendChartRef.value);

  riskLevelChart.setOption({
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["45%", "72%"],
        label: { color: "#1c2625" },
        data: Object.entries(stats.risk_level_distribution).map(([name, value]) => ({ name, value })),
      },
    ],
  });

  riskTypeChart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: Object.keys(stats.risk_type_distribution),
      axisLabel: { rotate: 25 },
    },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: Object.values(stats.risk_type_distribution),
        itemStyle: { color: "#145f59" },
      },
    ],
  });

  trendChart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: stats.daily_requests.map((item) => item.date),
    },
    yAxis: { type: "value" },
    series: [
      {
        type: "line",
        smooth: true,
        data: stats.daily_requests.map((item) => item.count),
        lineStyle: { color: "#d08a1e", width: 3 },
        itemStyle: { color: "#d08a1e" },
      },
    ],
  });
}

async function loadStats() {
  const data = await fetchDashboardStats();
  Object.assign(stats, data);
  await nextTick();
  renderCharts();
}

onMounted(() => {
  loadStats().catch(() => {});
  window.addEventListener("resize", renderCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", renderCharts);
  riskLevelChart?.dispose();
  riskTypeChart?.dispose();
  trendChart?.dispose();
});
</script>

<style scoped>
.chart-panel,
.table-panel {
  padding: 22px;
}

.chart-title {
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 700;
}
</style>
