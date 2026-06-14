import json
import re
import shutil
from pathlib import Path
from threading import Lock
from typing import Any


RULE_GROUP_FILE_PATH = Path(__file__).resolve().parents[2] / "data" / "rule_groups.json"
DEFAULT_RULE_GROUP_FILE_PATH = Path(__file__).resolve().parents[1] / "resources" / "rule_groups.default.json"
NON_LEARNABLE_CATEGORIES = {"privacy", "credential_leak", "sensitive_info"}
NON_LEARNABLE_CANDIDATE_PATTERNS = (
    r"^\s*(?:rm|del|sudo|chmod|chown|curl|wget|bash|sh|python|powershell|cmd)\b",
    r"\brm\s+-rf\b",
    r"\b(?:execute|run)\s+(?:this|the following)\b",
    r"(?:执行|运行)(?:这个|以下)?(?:命令|代码)",
    r"(?:帮我|请)?(?:执行|运行)",
    r"(?:给我|提供).*(?:命令|脚本|步骤)",
    r"(?:什么意思|是什么|如何防范|怎么防范|风险是什么|仅用于学习|仅用于测试|请勿执行|不要执行)",
    r"(?:^|[\s'\"`])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]*",
    r"[;&|]{1,2}",
    r"\$\(",
    r"`.+`",
    r"\b(?:select|union|insert|update|delete)\b.+\b(?:from|into|where)\b",
    r"\b(?:php|python|bash|sh|powershell)\b.+[({]",
    r"\b(?:payload|webshell|backdoor|exploit|sql injection|反弹\s*shell)\b",
)

_rule_group_cache: dict[str, Any] = {
    "mtime_ns": None,
    "config": None,
}
_rule_group_lock = Lock()


def _ensure_rule_group_file_permissions(path: Path) -> None:
    try:
        path.chmod(0o666)
    except OSError:
        pass


def ensure_rule_group_file() -> Path:
    RULE_GROUP_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not RULE_GROUP_FILE_PATH.exists():
        shutil.copyfile(DEFAULT_RULE_GROUP_FILE_PATH, RULE_GROUP_FILE_PATH)
    _ensure_rule_group_file_permissions(RULE_GROUP_FILE_PATH)
    return RULE_GROUP_FILE_PATH


def _build_regex_flags(flag_names: list[str]) -> int:
    flags = 0
    for flag_name in flag_names:
        if flag_name == "IGNORECASE":
            flags |= re.IGNORECASE
    return flags


def _load_rule_group_file() -> dict[str, Any]:
    path = ensure_rule_group_file()
    raw = json.loads(path.read_text(encoding="utf-8"))

    keyword_groups = []
    for group in raw.get("keyword_groups", []):
        keywords = []
        seen = set()
        for keyword in group.get("keywords", []):
            normalized = str(keyword).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            keywords.append(normalized)

        keyword_groups.append(
            {
                "name": group.get("name", "rule_group"),
                "category": group.get("category", "unknown"),
                "risk_level": group.get("risk_level", "medium"),
                "auto_learn": bool(group.get("auto_learn", False)),
                "keywords": keywords,
            }
        )

    regex_rules = []
    for rule in raw.get("regex_rules", []):
        pattern = str(rule.get("pattern", "")).strip()
        if not pattern:
            continue
        try:
            compiled = re.compile(pattern, _build_regex_flags(rule.get("flags", [])))
        except re.error:
            continue

        regex_rules.append(
            {
                "name": rule.get("name", "regex_rule"),
                "compiled_pattern": compiled,
                "pattern": pattern,
                "category": rule.get("category", "unknown"),
                "risk_level": rule.get("risk_level", "medium"),
            }
        )

    reason_priority = [
        (str(item.get("category", "")).strip(), str(item.get("reason", "")).strip())
        for item in raw.get("reason_priority", [])
        if str(item.get("category", "")).strip() and str(item.get("reason", "")).strip()
    ]

    return {
        "keyword_groups": keyword_groups,
        "regex_rules": regex_rules,
        "reason_priority": reason_priority,
    }


def get_rule_group_config(force_refresh: bool = False) -> dict[str, Any]:
    path = ensure_rule_group_file()
    mtime_ns = path.stat().st_mtime_ns
    if not force_refresh and _rule_group_cache["config"] is not None and _rule_group_cache["mtime_ns"] == mtime_ns:
        return _rule_group_cache["config"]

    with _rule_group_lock:
        mtime_ns = path.stat().st_mtime_ns
        if not force_refresh and _rule_group_cache["config"] is not None and _rule_group_cache["mtime_ns"] == mtime_ns:
            return _rule_group_cache["config"]

        config = _load_rule_group_file()
        _rule_group_cache["config"] = config
        _rule_group_cache["mtime_ns"] = mtime_ns
        return config


def _normalize_learning_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_keyword_candidates(text: str) -> list[str]:
    normalized = _normalize_learning_text(text)
    if not normalized:
        return []

    candidates: list[str] = []
    seen = set()
    segments = re.split(r"[\n\r。！？!?；;，,]", normalized)

    for segment in segments:
        candidate = segment.strip(" \"'`[](){}")
        if len(candidate) < 4:
            continue
        if len(candidate) > 80:
            candidate = candidate[:80].rstrip()
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(candidate)
        if len(candidates) >= 3:
            break

    if not candidates and len(normalized) <= 80:
        candidates.append(normalized)
    return [candidate for candidate in candidates if _is_learnable_keyword_candidate(candidate)]


def _is_learnable_keyword_candidate(candidate: str) -> bool:
    normalized = candidate.strip()
    if len(normalized) < 4:
        return False
    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in NON_LEARNABLE_CANDIDATE_PATTERNS):
        return False
    if normalized.count(" ") >= 8:
        return False
    return True


def learn_keywords_from_ai_detection(text: str, risk_types: list[str]) -> bool:
    learnable_categories = [
        category
        for category in risk_types
        if category and category not in NON_LEARNABLE_CATEGORIES
    ]
    if not learnable_categories:
        return False

    candidates = _extract_keyword_candidates(text)
    if not candidates:
        return False

    path = ensure_rule_group_file()
    updated = False

    with _rule_group_lock:
        raw = json.loads(path.read_text(encoding="utf-8"))
        groups = raw.get("keyword_groups", [])

        for group in groups:
            category = str(group.get("category", "")).strip()
            if category not in learnable_categories or not group.get("auto_learn", False):
                continue

            keywords = [str(item).strip() for item in group.get("keywords", []) if str(item).strip()]
            seen = {item.lower() for item in keywords}
            for candidate in candidates:
                key = candidate.lower()
                if key in seen:
                    continue
                keywords.append(candidate)
                seen.add(key)
                updated = True
            group["keywords"] = keywords

        if updated:
            path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _ensure_rule_group_file_permissions(path)
            _rule_group_cache["config"] = None
            _rule_group_cache["mtime_ns"] = None

    return updated
