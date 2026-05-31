import { createRouter, createWebHistory } from "vue-router";

import AuditLogsView from "../views/AuditLogs.vue";
import ChatView from "../views/Chat.vue";
import DashboardView from "../views/Dashboard.vue";
import RuleManageView from "../views/RuleManage.vue";
import SystemConfigView from "../views/SystemConfig.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/chat" },
    { path: "/chat", name: "chat", component: ChatView, meta: { title: "Chat 对话测试" } },
    { path: "/dashboard", name: "dashboard", component: DashboardView, meta: { title: "Dashboard 风险看板" } },
    { path: "/logs", name: "logs", component: AuditLogsView, meta: { title: "Audit Logs 审计日志" } },
    { path: "/rules", name: "rules", component: RuleManageView, meta: { title: "Rule Manage 规则管理" } },
    { path: "/config", name: "config", component: SystemConfigView, meta: { title: "System Config 系统配置" } },
  ],
});

export default router;
