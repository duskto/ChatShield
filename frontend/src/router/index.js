import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/chat" },
    {
      path: "/chat",
      name: "chat",
      component: () => import("../views/Chat.vue"),
      meta: { title: "Chat 对话测试" },
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("../views/Dashboard.vue"),
      meta: { title: "Dashboard 风险看板" },
    },
    {
      path: "/logs",
      name: "logs",
      component: () => import("../views/AuditLogs.vue"),
      meta: { title: "Audit Logs 审计日志" },
    },
    {
      path: "/rules",
      name: "rules",
      component: () => import("../views/RuleManage.vue"),
      meta: { title: "Rule Manage 规则管理" },
    },
    {
      path: "/config",
      name: "config",
      component: () => import("../views/SystemConfig.vue"),
      meta: { title: "System Config 系统配置" },
    },
  ],
});

export default router;
