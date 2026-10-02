"""Raiz do projeto e espera por pastas de rede."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturoEsgotado
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESPERA_REDE = 8


def caminho(valor: str) -> Path:
    bruto = Path(valor)
    if bruto.is_absolute():
        return bruto
    return RAIZ / bruto


def existe(pasta: Path, segundos: float = ESPERA_REDE) -> bool:
    pool = ThreadPoolExecutor(max_workers=1)
    futuro = pool.submit(pasta.exists)
    try:
        return bool(futuro.result(timeout=segundos))
    except FuturoEsgotado:
        return False
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
