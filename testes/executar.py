"""Roda a suíte Python e a suíte do navegador (modelos das telas)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def main() -> int:
    python = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.discover(str(RAIZ / "testes"), pattern="test_*.py", top_level_dir=str(RAIZ))
    )
    arquivos = sorted((RAIZ / "web" / "testes").glob("*.test.js"))
    telas = subprocess.run(
        ["node", "--test", *[str(arquivo.relative_to(RAIZ)) for arquivo in arquivos]],
        cwd=RAIZ,
        check=False,
    )
    if python.wasSuccessful() and telas.returncode == 0:
        return 0
    return 1


if __name__ == "__main__":
    sys.path.insert(0, str(RAIZ))
    raise SystemExit(main())
