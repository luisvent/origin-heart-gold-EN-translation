"""Keep the optional graphics environment aligned with the existing runtime pin."""
from pathlib import Path
import tomllib
import unittest

WORK = Path(__file__).resolve().parent.parent


class GraphicsPins(unittest.TestCase):
    def test_pillow_pin_agrees_between_project_runtime_and_lock(self):
        project = tomllib.loads((WORK/'pyproject.toml').read_text())
        lock = tomllib.loads((WORK/'uv.lock').read_text())
        runtime = [line.strip().lower() for line in (WORK/'tools/requirements-runtime.txt').read_text().splitlines()
                   if line.strip().lower().startswith('pillow==')]
        graphics = [value.lower() for value in project['dependency-groups']['graphics']
                    if value.lower().startswith('pillow==')]
        self.assertEqual(len(runtime), 1)
        self.assertEqual(graphics, runtime)
        packages = [p for p in lock['package'] if p['name'] == 'pillow']
        self.assertEqual(len(packages), 1)
        self.assertEqual('pillow==' + packages[0]['version'], runtime[0])


if __name__ == '__main__':
    unittest.main()
