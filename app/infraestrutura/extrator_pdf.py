"""Gera contrato.json a partir do PDF do termo.

O PDF permanece o documento. O JSON é só o índice que o painel lê:
número, fornecedor, vigência, valor e dotação saem do texto do termo.
Pago, gestor, fiscal e dia de pagamento não estão no PDF.
"""

from __future__ import annotations

import json
import re
import sys
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

from pypdf import PdfReader

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def texto_pdf(caminho: Path) -> str:
    leitor = PdfReader(str(caminho))
    bruto = "\n".join((pagina.extract_text() or "") for pagina in leitor.pages)
    linhas = []
    for linha in bruto.splitlines():
        s = linha.strip()
        if not s:
            continue
        if s.startswith(("PÁGINA", "PAGINA", "ASSINADO", "EXISTEM MAIS", "Verifique a autenticidade")):
            continue
        if s.startswith("-- ") and " of " in s:
            continue
        if s in ("GOVERNO DO ESTADO DO TOCANTINS", "AGÊNCIA DE TECNOLOGIA DA INFORMAÇÃO", "AGENCIA DE TECNOLOGIA DA INFORMACAO"):
            continue
        if re.match(r"^SGD\s", s):
            continue
        linhas.append(s)
    texto = "\n".join(linhas)
    texto = re.sub(r"-\n\s*", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def dinheiro(valor: str) -> float:
    return float(valor.replace(".", "").replace(",", "."))


def iso(dia: int, mes: int, ano: int) -> str:
    return date(ano, mes, dia).isoformat()


def somar_meses(inicio: date, meses: int) -> date:
    indice = inicio.month - 1 + meses
    ano = inicio.year + indice // 12
    mes = indice % 12 + 1
    dia = min(inicio.day, monthrange(ano, mes)[1])
    return date(ano, mes, dia) - timedelta(days=1)


def primeiro(texto: str, padrao: str) -> str | None:
    achado = re.search(padrao, texto, flags=re.IGNORECASE)
    if not achado:
        return None
    return re.sub(r"\s+", " ", achado.group(1)).strip(" ,.;")


def extrair_texto(texto: str, arquivo: str) -> dict:
    numero = primeiro(texto, r"TERMO DE CONTRATO\s+N.\s*(\d+/\d{4}(?:/[A-Z0-9]+)*)")
    partes = numero.split("/") if numero else []
    setor = partes[2] if len(partes) >= 3 else ""
    superintendencia = partes[3] if len(partes) >= 4 else ""

    fornecedor = primeiro(texto, r"empresa\s+(.+?)\s*,\s*pessoa jur.dica de direito privado")
    processo = primeiro(texto, r"PROCESSO\s+N.\s*:?\s*(\d{4}/\d+/\d+)")
    objeto = primeiro(
        texto,
        r"CLÁUSULA PRIMEIRA\s*-?\s*DO OBJETO\s+O presente contrato tem por objeto\s+(.+?)\s+PARÁGRAFO ÚNICO",
    )
    if objeto is None:
        objeto = primeiro(texto, r"tem por objeto\s+(.+?)\s+PARÁGRAFO")
    if objeto and objeto.casefold().startswith("a "):
        objeto = objeto[2:]
    if objeto:
        objeto = objeto[0].upper() + objeto[1:]

    modalidade = ""
    if re.search(r"preg[aã]o", texto, flags=re.IGNORECASE) and re.search(r"eletr[oô]nic", texto, flags=re.IGNORECASE):
        modalidade = "Pregão Eletrônico"
    elif re.search(r"\bdispensa\b", texto, flags=re.IGNORECASE):
        modalidade = "Dispensa"
    elif re.search(r"inexigibilidade", texto, flags=re.IGNORECASE):
        modalidade = "Inexigibilidade"

    assinatura = ""
    data_extenso = re.search(
        r"Aos\s+(\d{1,2})\s+dias\s+do\s+m.s\s+de\s+([A-Za-zçÇ]+)\s+de\s+(\d{4})",
        texto,
        flags=re.IGNORECASE,
    )
    inicio = ""
    fim = ""
    if data_extenso:
        mes = MESES.get(data_extenso.group(2).casefold().replace("ç", "c"))
        if mes is None:
            mes = MESES.get(data_extenso.group(2).casefold())
        if mes:
            dia = date(int(data_extenso.group(3)), mes, int(data_extenso.group(1)))
            assinatura = dia.isoformat()
            inicio = assinatura
            meses = primeiro(texto, r"vig.ncia de\s+(\d+)\s+\(")
            if meses:
                fim = somar_meses(dia, int(meses)).isoformat()

    valor = primeiro(texto, r"valor do presente Termo de Contrato .{0,12}? de\s+R\$\s*([\d.]+,\d{2})")
    if valor is None:
        valor = primeiro(texto, r"VALOR TOTAL\s+R\$\s*([\d.]+,\d{2})")

    funcao = primeiro(texto, r"Fun..o:\s*(\d+)")
    subfuncao = primeiro(texto, r"Subfun..o:\s*(\d+)")
    programa = primeiro(texto, r"Programa:\s*(\d+)")
    if funcao and subfuncao and programa:
        programa = f"{int(funcao):02d}.{int(subfuncao):03d}.{programa}"
    fonte = primeiro(texto, r"Fonte:\s*(\d+)")
    nd = primeiro(texto, r"Natureza:\s*([\d.]+)")

    return {
        "numero": numero or "",
        "fornecedor": fornecedor or "",
        "objeto": objeto or "",
        "setor": setor,
        "superintendencia": superintendencia,
        "processo": processo or "",
        "modalidade": modalidade,
        "assinatura": assinatura,
        "inicio": inicio,
        "fim": fim,
        "diaPagamento": None,
        "valor": dinheiro(valor) if valor else None,
        "pago": 0,
        "fonte": fonte or "",
        "programa": programa or "",
        "nd": nd or "",
        "renovavel": bool(re.search(r"podendo ser prorrogad", texto, flags=re.IGNORECASE)),
        "gestor": "",
        "fiscal": "",
        "arquivo": arquivo,
    }


def pdf_do_contrato(pasta: Path) -> Path | None:
    pdfs = sorted(p for p in pasta.glob("*.pdf") if p.is_file())
    if not pdfs:
        return None
    preferidos = [p for p in pdfs if "contrato" in p.name.casefold()]
    return preferidos[0] if preferidos else pdfs[0]


def extrair_arquivo(caminho: Path) -> dict:
    return extrair_texto(texto_pdf(caminho), caminho.name)


def gravar(destino: Path, contrato: dict) -> None:
    destino.write_text(json.dumps(contrato, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python -m app.infraestrutura.extrator_pdf <termo.pdf>")
    pdf = Path(sys.argv[1])
    if not pdf.is_file():
        raise SystemExit(f"Arquivo não encontrado: {pdf}")
    contrato = extrair_arquivo(pdf)
    destino = pdf.parent / "contrato.json"
    gravar(destino, contrato)
    print(destino)


if __name__ == "__main__":
    main()
