def safe_block_reply(stage: str) -> str:
    if stage == "input":
        return "该请求存在安全风险，已被 ChatShield 拦截。"
    if stage == "output":
        return "模型回复存在安全风险，已被 ChatShield 拦截。"
    return "请求处理失败，请稍后重试。"

