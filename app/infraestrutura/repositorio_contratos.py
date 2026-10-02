"""Lê a árvore <raiz>/<superintendência>/<contrato>/contrato.json."""

from __future__ import annotations

import json
from pathlib import Path

from app.dominio.contrato import ARQUIVO_CONTRATO, validar
from app.infraestrutura.caminhos import caminho, existe
from app.infraestrutura.extrator_pdf import extrair_arquivo, gravar, pdf_do_contrato


def carregar(config: dict) -> tuple[list[dict], list[dict], Path, list[dict]]:
    raiz = caminho(config["raizArquivos"])
    if not existe(raiz):
        return [], [{"numero": "", "faltando": [f"diretório indisponível ({raiz}). Confira se a unidade S: está conectada."]}], raiz, [{"caminho": str(raiz), "existe": False}]
    if not raiz.is_dir():
        return [], [{"numero": "", "faltando": [f"{raiz} não é uma pasta"]}], raiz, [{"caminho": str(raiz), "existe": False}]

    validos = []
    erros = []
    pastas = [{"caminho": str(raiz), "existe": True, "tipo": "raiz"}]
    vistos: set[tuple[str, str]] = set()
    supers = [p for p in raiz.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if not supers:
        return [], [{"numero": "", "faltando": [f"nenhuma pasta de superintendência em {raiz}"]}], raiz, pastas

    for super_dir in sorted(supers, key=lambda p: p.name.casefold()):
        pastas.append({"caminho": str(super_dir), "existe": True, "tipo": "superintendencia"})
        contratos = [p for p in super_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not contratos:
            erros.append({
                "numero": "",
                "superintendencia": super_dir.name,
                "faltando": ["nenhuma pasta de contrato"],
                "pasta": str(super_dir),
            })
            continue
        for contrato_dir in sorted(contratos, key=lambda p: p.name.casefold()):
            pastas.append({"caminho": str(contrato_dir), "existe": True, "tipo": "contrato"})
            registro = contrato_dir / ARQUIVO_CONTRATO
            item = _ler_item(registro, contrato_dir, super_dir.name, erros)
            if item is None:
                continue
            contrato, erro_item = validar(item, super_dir.name, contrato_dir, vistos)
            if erro_item:
                erros.append(erro_item)
            elif contrato:
                validos.append(contrato)
    return validos, erros, raiz, pastas


def _ler_item(registro: Path, contrato_dir: Path, superintendencia: str, erros: list[dict]) -> dict | None:
    if registro.is_file():
        try:
            with registro.open(encoding="utf-8-sig") as arquivo:
                return json.load(arquivo)
        except (OSError, json.JSONDecodeError) as erro:
            erros.append({
                "numero": contrato_dir.name,
                "superintendencia": superintendencia,
                "faltando": [f"{ARQUIVO_CONTRATO} ilegível ({erro})"],
                "pasta": str(contrato_dir),
            })
            return None
    pdf = pdf_do_contrato(contrato_dir)
    if pdf is None:
        erros.append({
            "numero": contrato_dir.name,
            "superintendencia": superintendencia,
            "faltando": [f"{ARQUIVO_CONTRATO} ou PDF do termo"],
            "pasta": str(contrato_dir),
        })
        return None
    try:
        item = extrair_arquivo(pdf)
        gravar(registro, item)
    except (OSError, ValueError) as erro:
        erros.append({
            "numero": contrato_dir.name,
            "superintendencia": superintendencia,
            "faltando": [f"PDF ilegível ({erro})"],
            "pasta": str(contrato_dir),
        })
        return None
    return item
