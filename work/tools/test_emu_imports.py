"""Static check: every `import emu_x` / `from emu_x import ...` in work/tools/emu_*.py names a module that exists."""
import ast
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


def emu_imports(path):
    """(line, module) of every import of an emu_* module anywhere in the file (also inside functions)."""
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out += [(node.lineno, a.name.split(".")[0]) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.append((node.lineno, node.module.split(".")[0]))
    return [(n, m) for n, m in out if m.startswith("emu_")]


class EmuImportsExist(unittest.TestCase):
    def test_no_dangling_emu_import(self):
        missing = [f"{p.name}:{n} imports {m}" for p in sorted(TOOLS.glob("emu_*.py")) for n, m in emu_imports(p)
                   if not (TOOLS / f"{m}.py").exists()]
        self.assertEqual(missing, [])

    def test_checker_sees_imports(self):
        self.assertTrue(any(m == "emu_harness" for _, m in emu_imports(TOOLS / "emu_fixes.py")))


if __name__ == "__main__":
    unittest.main()
