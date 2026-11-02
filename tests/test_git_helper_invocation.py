"""Real Git -> Python argument parsing, without Studio/GitHub credentials."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import studio_git as module


class HelperInvocationTests(unittest.TestCase):
    def test_git_appended_operation_works_with_the_actual_parser(self):
        tree = ast.parse(Path(module.__file__).read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        statements = []
        for node in main.body:
            if isinstance(node, ast.Try):
                break
            statements.append(ast.unparse(node))
        # Extract only the production argument parser. No authorization, keychain
        # access, private credential action or network calls are executed.
        parser_source = '\n'.join(statements)
        fixture = ('import argparse, sys\n' + parser_source + '\n'
                   'assert args.action == "credential"\n'
                   'assert args.project_id == "test-project"\n'
                   'if args.credential_operation == "get":\n'
                   '    print("username=test-fixture\\npassword=synthetic-fixture\\n")\n')
        interpreters = [sys.executable]
        apple = Path('/Library/Developer/CommandLineTools/usr/bin/python3')
        if apple.is_file() and str(apple) not in interpreters:
            interpreters.append(str(apple))
        with tempfile.TemporaryDirectory(prefix='studio helper test ') as directory:
            script = Path(directory) / 'credential parser.py'
            script.write_text(fixture)
            env = dict(os.environ)
            for key in list(env):
                if key.startswith('GIT_'):
                    del env[key]
            env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
            for interpreter in interpreters:
                with self.subTest(interpreter=interpreter), \
                        patch.object(module, '__file__', str(script)), \
                        patch.object(module.sys, 'executable', interpreter):
                    command = module.helper('test-project')
                result = subprocess.run(['git', '-c', 'credential.helper=', '-c',
                    'credential.helper=' + command, '-c', 'credential.useHttpPath=true',
                    'credential', 'fill'], input='protocol=https\nhost=example.invalid\npath=example/client.git\n\n',
                    cwd=directory, env=env, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('password=synthetic-fixture', result.stdout)


if __name__ == '__main__':
    unittest.main()
