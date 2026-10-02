"""Caso de uso que monta o painel consumido pelas telas."""

from __future__ import annotations

from app.infraestrutura.caminhos import caminho
from app.infraestrutura.repositorio_contratos import carregar


def montar_painel(config: dict) -> dict:
    contratos, erros, registro, pastas = carregar(config)
    usuario = config.get("usuario") or {}
    return {
        "orgao": config["orgao"],
        "orgaoNome": config.get("orgaoNome") or config["orgao"],
        "usuario": {
            "nome": str(usuario.get("nome") or ""),
            "cargo": str(usuario.get("cargo") or ""),
        },
        "ilustrativo": bool(config.get("dadosIlustrativos")),
        "registro": str(registro),
        "raizArquivos": str(caminho(config["raizArquivos"])),
        "regras": {
            "janelaRenovacaoDias": int(config["regras"]["janelaRenovacaoDias"]),
            "limiteExecucao": float(config["regras"]["limiteExecucao"]),
        },
        "modulos": config["modulos"],
        "pastas": pastas,
        "contratos": contratos,
        "erros": erros,
    }
