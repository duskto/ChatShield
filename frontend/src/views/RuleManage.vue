<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">规则管理</h1>
        <p class="page-subtitle">数据库自定义规则会叠加在系统内置规则之上，立即参与聊天输入和输出检测。</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">新增规则</el-button>
    </div>

    <div class="page-card tip-card">
      <el-alert
        title="内置规则仍然保留在后端代码中，这里管理的是额外补充的自定义规则。"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <div class="page-card table-wrap">
      <el-table :data="rules" height="560">
        <el-table-column prop="name" label="规则名称" min-width="180" />
        <el-table-column prop="category" label="分类" width="150" />
        <el-table-column prop="match_type" label="匹配方式" width="120" />
        <el-table-column prop="risk_level" label="风险等级" width="120" />
        <el-table-column prop="enabled" label="启用" width="100">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="toggleRule(row, $event)" />
          </template>
        </el-table-column>
        <el-table-column prop="pattern" label="关键词 / 正则" min-width="280" show-overflow-tooltip />
        <el-table-column prop="description" label="说明" min-width="220" show-overflow-tooltip />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-row">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="removeRule(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增规则' : '编辑规则'" width="720px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：custom_injection_rule" />
        </el-form-item>
        <el-form-item label="规则分类" prop="category">
          <el-select v-model="form.category" placeholder="选择分类">
            <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配方式" prop="match_type">
          <el-radio-group v-model="form.match_type">
            <el-radio-button label="keyword">keyword</el-radio-button>
            <el-radio-button label="regex">regex</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="风险等级" prop="risk_level">
          <el-select v-model="form.risk_level">
            <el-option label="low" value="low" />
            <el-option label="medium" value="medium" />
            <el-option label="high" value="high" />
            <el-option label="critical" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>
        <el-form-item label="匹配内容" prop="pattern">
          <el-input
            v-model="form.pattern"
            type="textarea"
            :rows="4"
            :placeholder="form.match_type === 'regex' ? '输入正则表达式' : '输入要命中的关键词'"
          />
        </el-form-item>
        <el-form-item label="规则说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="说明规则用途和适用场景" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import {
  ElAlert,
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElRadioButton,
  ElRadioGroup,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
} from "element-plus";

import { createRule, deleteRule, fetchRules, updateRule } from "../api/rules";

const categoryOptions = [
  "prompt_injection",
  "jailbreak",
  "privacy",
  "credential_leak",
  "cyber_abuse",
  "malware",
  "illegal",
  "fraud",
  "violence",
  "sexual",
  "hate",
  "self_harm",
  "sensitive_info",
  "unknown",
];

const rules = ref([]);
const dialogVisible = ref(false);
const dialogMode = ref("create");
const saving = ref(false);
const editingId = ref(null);
const formRef = ref(null);

const form = reactive({
  name: "",
  category: "prompt_injection",
  pattern: "",
  match_type: "keyword",
  risk_level: "medium",
  enabled: true,
  description: "",
});

const formRules = {
  name: [{ required: true, message: "请输入规则名称", trigger: "blur" }],
  category: [{ required: true, message: "请选择规则分类", trigger: "change" }],
  pattern: [{ required: true, message: "请输入匹配内容", trigger: "blur" }],
  match_type: [{ required: true, message: "请选择匹配方式", trigger: "change" }],
  risk_level: [{ required: true, message: "请选择风险等级", trigger: "change" }],
};

function resetForm() {
  form.name = "";
  form.category = "prompt_injection";
  form.pattern = "";
  form.match_type = "keyword";
  form.risk_level = "medium";
  form.enabled = true;
  form.description = "";
  editingId.value = null;
}

async function loadRules() {
  try {
    rules.value = await fetchRules();
  } catch (error) {
    ElMessage.error(error.message);
  }
}

function openCreateDialog() {
  dialogMode.value = "create";
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(rule) {
  dialogMode.value = "edit";
  editingId.value = rule.id;
  form.name = rule.name;
  form.category = rule.category;
  form.pattern = rule.pattern;
  form.match_type = rule.match_type;
  form.risk_level = rule.risk_level;
  form.enabled = rule.enabled;
  form.description = rule.description || "";
  dialogVisible.value = true;
}

async function submitRule() {
  try {
    await formRef.value.validate();
  } catch {
    return;
  }

  saving.value = true;
  try {
    const payload = {
      name: form.name,
      category: form.category,
      pattern: form.pattern,
      match_type: form.match_type,
      risk_level: form.risk_level,
      enabled: form.enabled,
      description: form.description || null,
    };

    if (dialogMode.value === "create") {
      await createRule(payload);
      ElMessage.success("规则已创建");
    } else {
      await updateRule(editingId.value, payload);
      ElMessage.success("规则已更新");
    }

    dialogVisible.value = false;
    await loadRules();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    saving.value = false;
  }
}

async function toggleRule(rule, enabled) {
  try {
    await updateRule(rule.id, { enabled });
    rule.enabled = enabled;
    ElMessage.success(enabled ? "规则已启用" : "规则已停用");
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function removeRule(rule) {
  try {
    await ElMessageBox.confirm(`确认删除规则「${rule.name}」吗？`, "删除规则", {
      type: "warning",
    });
    await deleteRule(rule.id);
    ElMessage.success("规则已删除");
    await loadRules();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error.message || "删除失败");
    }
  }
}

onMounted(() => {
  loadRules();
});
</script>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-end;
}

.tip-card,
.table-wrap {
  padding: 20px;
}

.action-row {
  display: flex;
  gap: 8px;
}

@media (max-width: 1024px) {
  .page-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
