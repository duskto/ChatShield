<template>
  <el-tag :type="tagType" effect="dark" round>{{ label }}</el-tag>
</template>

<script setup>
import { computed } from "vue";
import { ElTag } from "element-plus";

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  level: {
    type: String,
    default: "low",
  },
});

const tagType = computed(() => {
  if (props.level === "low") return "success";
  if (props.level === "medium") return "warning";
  return "danger";
});
</script>
