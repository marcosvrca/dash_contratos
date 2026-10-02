"""Hash de senha com PBKDF2."""

from __future__ import annotations

import hashlib
import hmac
import secrets

RODADAS = 200_000


def hash_senha(senha: str) -> str:
    sal = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, RODADAS)
    return "pbkdf2$" + sal.hex() + "$" + derivado.hex()


def senha_confere(informada: str, gravada: str) -> bool:
    partes = str(gravada or "").split("$")
    if len(partes) != 3 or partes[0] != "pbkdf2":
        return False
    try:
        sal = bytes.fromhex(partes[1])
        esperado = bytes.fromhex(partes[2])
    except ValueError:
        return False
    calculado = hashlib.pbkdf2_hmac("sha256", informada.encode("utf-8"), sal, RODADAS)
    return hmac.compare_digest(calculado, esperado)
