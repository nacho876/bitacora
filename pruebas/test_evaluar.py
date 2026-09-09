import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evaluar_conversaciones as runner
from evaluar_conversaciones import extract_jsonl, usage_from


class EvaluarTests(unittest.TestCase):
    def test_usage_preserves_zero_and_absence(self):
        self.assertEqual(usage_from({"usage": {"input_tokens": 0, "output_tokens": 2}}),
                         {"input_tokens": 0, "output_tokens": 2})
        self.assertEqual(usage_from({"type": "message"}), {})

    def test_extracts_nested_cache_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "run.jsonl"
            path.write_text(json.dumps({"message": {"usage": {"input_tokens": 99}}}) + "\nno-json\n" + json.dumps({"type": "result", "model": "sonnet-effective", "usage": {"input_tokens": 4, "cache_read_input_tokens": 3, "output_tokens": 2}}), encoding="utf-8")
            result = extract_jsonl(path)
        self.assertEqual(result["usage"], {"input_tokens": 4, "cache_read_tokens": 3, "output_tokens": 2,
                                            "cache_creation_tokens": None})
        self.assertEqual(result["errors"], ["línea JSON inválida"])
        self.assertEqual(result["models"], ["sonnet-effective"])

    def test_result_error_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "error.jsonl"
            path.write_text(json.dumps({"type": "result", "is_error": True, "result": "denied"}), encoding="utf-8")
            result = extract_jsonl(path)
        self.assertEqual(result["errors"], ["denied"])

    def test_preserves_thinking_model_usage_and_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rich.jsonl"
            path.write_text("\n".join([json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read"}]}}), json.dumps({"type": "result", "usage": {"output_tokens": 8, "output_tokens_details": {"thinking_tokens": 3}}, "modelUsage": {"main": {"outputTokens": 8}, "helper": {"outputTokens": 1}}})]), encoding="utf-8")
            result = extract_jsonl(path)
        self.assertEqual(result["thinking_tokens"], 3)
        self.assertEqual(result["tools"], {"count": 1, "names": ["Read"]})
        self.assertEqual(result["model_usage"], [{"main": {"outputTokens": 8}, "helper": {"outputTokens": 1}}])

    def test_find_executable_prefers_explicit_path(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / "claude.exe"; exe.touch()
            self.assertEqual(runner.find_executable(str(exe)), exe)

    def test_timeout_marks_nonzero_and_preserves_fixture(self):
        class TimeoutProcess:
            returncode = None
            def communicate(self, prompt=None, timeout=None):
                if timeout: raise runner.subprocess.TimeoutExpired("claude", timeout)
                return (None, None)
            def kill(self): pass
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "out"; exe = Path(folder) / "claude.exe"; exe.touch()
            real_popen = runner.subprocess.Popen
            def popen(args, **kwargs):
                return real_popen(args, **kwargs) if args[0] == "git" else TimeoutProcess()
            with patch.object(runner.subprocess, "Popen", side_effect=popen):
                code = runner.run_fixture("sin_tema", "test", "medium", output, runner.ROOT, exe)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            preserved = (output / "fixture-final").is_dir()
        self.assertEqual(code, 1)
        self.assertEqual(manifest["turns"][0]["status"], "timeout")
        self.assertTrue(preserved)


if __name__ == "__main__":
    unittest.main()
