<template>
  <div class="page-shell">
    <div>
      <h1 class="page-title">审计日志</h1>
      <p class="page-subtitle">按风险等级、风险类型和拦截阶段筛选历史请求。</p>
    </div>

    <div class="page-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="风险等级">
          <el-select v-model="filters.risk_level" clearable placeholder="全部">
            <el-option label="low" value="low" />
            <el-option label="medium" value="medium" />
            <el-option label="high" value="high" />
            <el-option label="critical" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险类型">
          <el-input v-model="filters.risk_type" clearable placeholder="如 prompt_injection" />
        </el-form-item>
        <el-form-item label="拦截阶段">
          <el-select v-model="filters.blocked_stage" clearable placeholder="全部">
            <el-option label="input" value="input" />
            <el-option label="output" value="output" />
            <el-option label="none" value="none" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" clearable placeholder="输入关键词搜索" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="page-card table-wrap">
      <el-table :data="items" height="520">
        <el-table-column prop="created_at" label="时间" min-width="180" />
        <el-table-column prop="blocked_stage" label="阶段" width="100" />
        <el-table-column prop="input_risk_level" label="输入等级" width="110" />
        <el-table-column prop="output_risk_level" label="输出等级" width="110" />
        <el-table-column prop="user_message" label="用户输入" min-width="260" show-overflow-tooltip />
        <el-table-column prop="reason" label="原因" min-width="240" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row.id)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="日志详情" width="920px">
      <template v-if="detail">
        <div class="detail-grid">
          <div class="detail-block">
            <div class="detail-label">用户输入</div>
            <div class="detail-content">{{ detail.user_message }}</div>
          </div>
          <div class="detail-block">
            <div class="detail-label">模型原始回复</div>
            <div class="detail-content">{{ detail.model_reply }}</div>
          </div>
          <div class="detail-block">
            <div class="detail-label">最终回复</div>
            <div class="detail-content">{{ detail.final_reply }}</div>
          </div>
          <div class="detail-block">
            <div class="detail-label">输入检测结果</div>
            <pre class="detail-code">{{ formatJson(detail.input_rule_result) }}</pre>
            <pre class="detail-code">{{ formatJson(detail.input_api_result) }}</pre>
          </div>
          <div class="detail-block">
            <div class="detail-label">输出检测结果</div>
            <pre class="detail-code">{{ formatJson(detail.output_rule_result) }}</pre>
            <pre class="detail-code">{{ formatJson(detail.output_api_result) }}</pre>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
} from "element-plus";

import { fetchLogDetail, fetchLogs } from "../api/logs";

const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const detailVisible = ref(false);
const detail = ref(null);

const filters = reactive({
  risk_level: "",
  risk_type: "",
  blocked_stage: "",
  keyword: "",
});

async function loadLogs() {
  try {
    const data = await fetchLogs({
      ...filters,
      page: page.value,
      page_size: pageSize.value,
    });
    items.value = data.items;
    total.value = data.total;
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function openDetail(id) {
  try {
    detail.value = await fetchLogDetail(id);
    detailVisible.value = true;
  } catch (error) {
    ElMessage.error(error.message);
  }
}

function handlePageChange(nextPage) {
  page.value = nextPage;
  loadLogs();
}

function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.filter-card,
.table-wrap {
  padding: 20px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding-top: 18px;
}

.detail-grid {
  display: grid;
  gap: 16px;
}

.detail-block {
  padding: 16px;
  border-radius: 16px;
  background: rgba(20, 95, 89, 0.04);
  border: 1px solid rgba(20, 95, 89, 0.12);
}

.detail-label {
  margin-bottom: 8px;
  font-weight: 700;
}

.detail-content {
  white-space: pre-wrap;
  line-height: 1.7;
}

.detail-code {
  margin: 12px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
