"""Regras do contrato que o painel aceita."""

from __future__ import annotations

import re
from pathlib import Path

DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OBRIGATORIOS = ("numero", "fornecedor", "setor", "inicio", "fim", "valor")
ARQUIVO_CONTRATO = "contrato.json"
CAMPOS_TEXTO = (
    "fiscal",
    "gestor",
    "objeto",
    "processo",
    "modalidade",
    "fonte",
    "programa",
    "nd",
    "fornecedor",
    "setor",
)


def validar(item: dict, superintendencia: str, pasta: Path, vistos: set[tuple[str, str]]) -> tuple[dict | None, dict | None]:
    if not isinstance(item, dict):
        return None, {"numero": "", "superintendencia": superintendencia, "faltando": ["objeto"], "pasta": str(pasta)}
    numero = str(item.get("numero") or pasta.name).strip()
    faltando = [campo for campo in OBRIGATORIOS if campo != "numero" and item.get(campo) in (None, "")]
    if not numero:
        faltando.append("numero")
    for campo in ("inicio", "fim", "assinatura"):
        valor = item.get(campo)
        if valor and not DATA_RE.match(str(valor)):
            faltando.append(campo + " (use AAAA-MM-DD)")
    chave = (superintendencia, numero)
    if numero and chave in vistos:
        faltando.append("numero duplicado na superintendência")
    if faltando:
        return None, {"numero": numero, "superintendencia": superintendencia, "faltando": faltando, "pasta": str(pasta)}
    contrato = dict(item)
    contrato["numero"] = numero
    contrato["superintendencia"] = superintendencia
    contrato["id"] = f"{superintendencia}/{numero}"
    contrato["pasta"] = str(pasta)
    contrato["valor"] = float(contrato["valor"])
    contrato["pago"] = float(contrato.get("pago") or 0)
    dia = contrato.get("diaPagamento")
    contrato["diaPagamento"] = None if dia in (None, "") else int(dia)
    contrato["renovavel"] = bool(contrato.get("renovavel"))
    for campo in CAMPOS_TEXTO:
        if contrato.get(campo) is None:
            contrato[campo] = ""
    vistos.add(chave)
    return contrato, None
