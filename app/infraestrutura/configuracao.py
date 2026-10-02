"""Leitura e gravação do config.json."""

from __future__ import annotations

import json

from app.infraestrutura.caminhos import RAIZ
from app.infraestrutura.senha import hash_senha

ARQUIVO = RAIZ / "config.json"


def gravar(config: dict) -> None:
    texto = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    ARQUIVO.write_text(texto, encoding="utf-8")


def preparar_acesso(config: dict) -> str | None:
    acesso = config.get("acesso")
    if not isinstance(acesso, dict):
        acesso = {}
        config["acesso"] = acesso
    usuario = str(acesso.get("usuario") or "admin").strip() or "admin"
    acesso["usuario"] = usuario
    senha = acesso.get("senha")
    if not isinstance(senha, str) or not senha.strip():
        import secrets

        clara = secrets.token_urlsafe(12)
        acesso["senha"] = hash_senha(clara)
        gravar(config)
        return clara
    if not senha.startswith("pbkdf2$"):
        acesso["senha"] = hash_senha(senha.strip())
        gravar(config)
    return None


def ler() -> dict:
    with ARQUIVO.open(encoding="utf-8-sig") as arquivo:
        config = json.load(arquivo)
    if "raizArquivos" not in config:
        raise SystemExit("config.json precisa do campo raizArquivos.")
    config.setdefault("orgao", "ATI")
    config.setdefault("orgaoNome", "Agência de Tecnologia da Informação do Tocantins")
    config.setdefault("usuario", {})
    config.setdefault("host", "127.0.0.1")
    config.setdefault("porta", 8765)
    config.setdefault("dadosIlustrativos", False)
    config.setdefault("regras", {})
    config["regras"].setdefault("janelaRenovacaoDias", 120)
    config["regras"].setdefault("limiteExecucao", 0.85)
    config.setdefault("modulos", [])
    return config
