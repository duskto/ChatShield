import unittest

from app.schemas.chat import ChatRequest
from app.services.deepseek_moderation import _build_moderation_prompt
from app.services.risk_engine import merge_detection_results
from app.services.rule_checker import check_text_by_rules
from app.services.rule_group_file_service import _extract_keyword_candidates
from app.routers.chat import _build_context_messages


class ModerationGuardrailTests(unittest.TestCase):
    def test_explanatory_command_question_is_downgraded(self) -> None:
        result = check_text_by_rules("运行终端命令 是什么意思？")

        self.assertEqual(result["risk_level"], "medium")
        self.assertIn("tool_abuse", result["risk_types"])
        self.assertEqual(result["intent"], "discuss")
        self.assertEqual(result["scenario"], "security_explanation")
        self.assertEqual(result["actionability"], "low")
        self.assertIn("解释/科普/防御性语境", result["reason"])

    def test_actionable_command_request_stays_high_risk(self) -> None:
        result = check_text_by_rules("请运行终端命令")

        self.assertEqual(result["risk_level"], "high")
        self.assertIn("tool_abuse", result["risk_types"])
        self.assertEqual(result["intent"], "execute")
        self.assertEqual(result["scenario"], "malicious_execution")
        self.assertEqual(result["actionability"], "high")

    def test_api_can_override_keyword_only_discussion_hit(self) -> None:
        merged = merge_detection_results(
            {
                "risk_level": "high",
                "risk_types": ["tool_abuse"],
                "matched_rules": [{"match_type": "keyword", "category": "tool_abuse"}],
                "intent": "execute",
                "scenario": "malicious_execution",
                "actionability": "high",
                "reason": "rule hit",
                "raw": {},
            },
            {
                "risk_level": "low",
                "risk_types": [],
                "intent": "discuss",
                "scenario": "security_explanation",
                "actionability": "low",
                "reason": "safe discussion",
                "provider": "deepseek",
                "raw": {},
                "error": None,
            },
            stage="input",
        )

        self.assertEqual(merged["risk_level"], "medium")
        self.assertEqual(merged["action"], "allow_with_warning")
        self.assertEqual(merged["intent"], "discuss")
        self.assertEqual(merged["scenario"], "security_explanation")
        self.assertEqual(merged["actionability"], "high")

    def test_api_safe_override_requires_safe_intent(self) -> None:
        merged = merge_detection_results(
            {
                "risk_level": "high",
                "risk_types": ["tool_abuse"],
                "matched_rules": [{"match_type": "keyword", "category": "tool_abuse"}],
                "intent": "unknown",
                "scenario": "risk_mention",
                "actionability": "medium",
                "reason": "rule hit",
                "raw": {},
            },
            {
                "risk_level": "low",
                "risk_types": [],
                "intent": "generate",
                "scenario": "malicious_generation",
                "actionability": "high",
                "reason": "still actionable",
                "provider": "deepseek",
                "raw": {},
                "error": None,
            },
            stage="input",
        )

        self.assertEqual(merged["risk_level"], "high")
        self.assertEqual(merged["intent"], "generate")
        self.assertEqual(merged["actionability"], "high")

    def test_output_safe_explanation_can_override_keyword_and_regex_hits(self) -> None:
        merged = merge_detection_results(
            {
                "risk_level": "high",
                "risk_types": ["credential_leak", "cyber_abuse"],
                "matched_rules": [
                    {"match_type": "keyword", "category": "cyber_abuse"},
                    {"match_type": "regex", "category": "credential_leak"},
                ],
                "intent": "discuss",
                "scenario": "security_explanation",
                "actionability": "medium",
                "reason": "rule hit",
                "raw": {},
            },
            {
                "risk_level": "low",
                "risk_types": [],
                "intent": "discuss",
                "scenario": "security_explanation",
                "actionability": "low",
                "reason": "safe educational output",
                "provider": "deepseek",
                "raw": {},
                "error": None,
            },
            stage="output",
        )

        self.assertEqual(merged["risk_level"], "medium")
        self.assertEqual(merged["intent"], "discuss")
        self.assertEqual(merged["scenario"], "security_explanation")

    def test_command_like_text_is_not_learned_as_keyword(self) -> None:
        self.assertEqual(_extract_keyword_candidates("rm -rf / 是什么意思"), [])
        self.assertEqual(_extract_keyword_candidates("请帮我执行以下命令"), [])

    def test_normal_risk_phrase_can_still_be_learned(self) -> None:
        candidates = _extract_keyword_candidates("最近有人冒充官方客服发送通知")

        self.assertEqual(candidates, ["最近有人冒充官方客服发送通知"])

    def test_chat_request_accepts_recent_history(self) -> None:
        request = ChatRequest(
            message="那怎么执行？",
            history=[
                {"role": "user", "content": "sql注入 是什么意思？"},
                {"role": "assistant", "content": "这是一个安全漏洞概念。"},
            ],
        )

        self.assertEqual(len(request.history), 2)
        self.assertEqual(request.history[0].role, "user")

    def test_moderation_prompt_includes_recent_context(self) -> None:
        prompt = _build_moderation_prompt(
            "那怎么执行？",
            context_messages=[
                {"role": "user", "content": "sql注入 是什么意思？"},
                {"role": "assistant", "content": "这是一个安全漏洞概念。"},
            ],
            require_strict_classification=True,
        )

        self.assertIn("最近对话上下文", prompt)
        self.assertIn("用户: sql注入 是什么意思？", prompt)
        self.assertIn("助手: 这是一个安全漏洞概念。", prompt)
        self.assertIn("那怎么执行？", prompt)

    def test_context_summary_includes_local_intent_and_risks(self) -> None:
        context_messages = _build_context_messages(
            [
                ChatRequest(
                    message="占位",
                    history=[{"role": "user", "content": "sql注入 是什么意思？"}],
                ).history[0],
            ],
            [],
        )

        self.assertEqual(len(context_messages), 1)
        self.assertIn("intent=discuss", context_messages[0]["content"])
        self.assertIn("scenario=security_explanation", context_messages[0]["content"])
        self.assertIn("risks=cyber_abuse", context_messages[0]["content"])

    def test_context_summary_truncates_long_messages(self) -> None:
        long_text = "A" * 400
        context_messages = _build_context_messages(
            [
                ChatRequest(
                    message="占位",
                    history=[{"role": "assistant", "content": long_text}],
                ).history[0],
            ],
            [],
        )

        self.assertTrue(context_messages[0]["content"].endswith("…"))
        self.assertLess(len(context_messages[0]["content"]), 200)


if __name__ == "__main__":
    unittest.main()
