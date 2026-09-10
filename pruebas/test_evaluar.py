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

class RobustezTests(unittest.TestCase):
    def parse(self, events):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'out.jsonl'
            path.write_text('\n'.join(json.dumps(e) for e in events), encoding='utf-8')
            return extract_jsonl(path)

    def test_incomplete_streams(self):
        for events in ([], [{'type':'system'}], [{'type':'assistant','message':{'content':[{'type':'text','text':'hola'}]}}], [{'type':'result','result':'  '}]):
            with self.subTest(events=events):
                self.assertEqual(self.parse(events)['status'], 'incomplete')

    def test_success_and_zero_without_double_count(self):
        result = self.parse([{'type':'assistant','message':{'usage':{'input_tokens':9}}}, {'type':'result','result':'Hola','usage':{'input_tokens':0}}])
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['usage']['input_tokens'], 0)
        self.assertIsNone(result['usage']['output_tokens'])

    def test_unexpected_types_reported(self):
        for event in (None, [], {'message':None}, {'message':[]}, {'message':{'content':None}}, {'type':'result','usage':None}, {'type':'result','usage':{'output_tokens_details':[]}}, {'modelUsage':[]}):
            with self.subTest(event=event):
                self.assertTrue(self.parse([event])['errors'])

    def test_result_must_be_final_event(self):
        self.assertEqual(self.parse([{'type':'result','result':'Hola'}, {'type':'assistant'}])['status'], 'incomplete')

    def test_invalid_result_fields_reported(self):
        for event in ({'type':'result','result':[]}, {'type':'result','result':'Hola','is_error':[]}):
            self.assertEqual(self.parse([event])['status'], 'error')

    def test_portable_executable(self):
        with patch.object(runner.shutil, 'which', side_effect=lambda name: '/bin/claude' if name == 'claude' else None):
            with patch.dict(runner.os.environ, {}, clear=True):
                self.assertEqual(runner.find_executable(), Path('/bin/claude'))

    def test_invalid_explicit_path_does_not_fallback(self):
        with patch.object(runner.shutil, 'which', return_value='other'):
            with self.assertRaises(ValueError):
                runner.find_executable('missing-cli-never-exists')

    def test_empty_cli_nonzero(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'empty.jsonl'; path.touch()
            result = runner.subprocess.run([sys.executable, str(runner.ROOT/'scripts/evaluar_conversaciones.py'), '--jsonl', str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr)

class EncodingTests(unittest.TestCase):
    INVALID = b'{"type":"result","result":"hola \xff","usage":{"input_tokens":0}}\n'

    def test_invalid_utf8_reports_error_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'invalid.jsonl'
            path.write_bytes(self.INVALID)
            result = extract_jsonl(path)
            self.assertEqual(path.read_bytes(), self.INVALID)
        self.assertEqual(result['status'], 'error')
        self.assertTrue(any('UTF-8' in error for error in result['errors']))
        self.assertTrue(all(value is None for value in result['usage'].values()))

    def test_invalid_utf8_cli_nonzero_without_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'invalid.jsonl'
            path.write_bytes(self.INVALID)
            result = runner.subprocess.run([sys.executable, str(runner.ROOT/'scripts/evaluar_conversaciones.py'), '--jsonl', str(path)], capture_output=True, text=True)
            self.assertEqual(path.read_bytes(), self.INVALID)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'error')


class RunnerEvidenceTests(unittest.TestCase):
    def simulate(self, mode):
        commands = []
        class Process:
            returncode = 0
            def __init__(self, args, **kwargs):
                self.version = '--version' in args
                if not self.version:
                    commands.append(args)
                    self.args = args
                    if mode == 'startup': raise OSError('synthetic startup failure')
                    event = {'type':'result','result':'OK','usage':{'input_tokens':0}}
                    if mode == 'error': event['is_error'] = True
                    if mode != 'empty': kwargs['stdout'].write(json.dumps(event)+'\n')
                    if mode == 'nonzero': self.returncode = 9
            def communicate(self, prompt=None, timeout=None):
                if self.version: return ('test-version\n', '')
                if mode == 'timeout' and timeout: raise runner.subprocess.TimeoutExpired('claude', timeout)
                return (None,None)
            def kill(self): pass
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'out'; exe=Path(folder)/'claude.exe';exe.touch()
            real_popen=runner.subprocess.Popen
            def popen(args, **kwargs):
                return real_popen(args,**kwargs) if args[0]=='git' else Process(args,**kwargs)
            with patch.object(runner.subprocess,'Popen',side_effect=popen):
                code=runner.run_fixture('sin_tema','test','medium',output,runner.ROOT,exe)
            manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
            self.assertTrue((output/'fixture-final/AGENTS.md').exists())
            self.assertTrue((output/'turn-01-stderr.txt').exists())
        manifest["_test_commands"] = commands
        return code, manifest

    def test_supported_cli_flags(self):
        _, manifest = self.simulate("success")
        for command in manifest["_test_commands"]:
            self.assertNotIn("--restricted", command)
            self.assertIn("--safe-mode", command)
            self.assertIn("dontAsk", command)
            self.assertIn("--strict-mcp-config", command)

    def test_status_preserves_process_failures(self):
        for mode, status in [('empty','incomplete'),('startup','startup_error'),('error','error'),('timeout','timeout'),('nonzero','error')]:
            with self.subTest(mode=mode):
                code, manifest=self.simulate(mode)
                self.assertEqual(code,1)
                self.assertEqual(manifest['turns'][0]['status'],status)

    def test_fingerprints_version_and_success(self):
        code,manifest=self.simulate('success')
        self.assertEqual(code,0)
        self.assertEqual(manifest['executable_version'],'test-version')
        for relative in ('AGENTS.md','CLAUDE.md','.cursor/rules/burbuja.mdc','bitacora/PLANTILLA.md','guias/contraste.md','guias/memoria.md'):
            self.assertEqual(manifest['protocol_hashes'][relative],runner.sha(runner.ROOT/relative))
        self.assertEqual(manifest['rubric'],'not_evaluated')

    def test_invalid_run_effort_rejected_before_launch(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(runner,'find_executable') as find:
            with self.assertRaises(ValueError):
                runner.run_fixture('sin_tema','test','unknown',Path(folder)/'unused',runner.ROOT)
            find.assert_not_called()


if __name__ == "__main__":
    unittest.main()
