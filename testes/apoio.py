"""Peças compartilhadas: contrato de exemplo e servidor temporário."""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.aplicacao.sessao import ServicoSessao
from app.apresentacao.http import fabricar_manipulador
from app.infraestrutura.senha import hash_senha


def contrato(**extras) -> dict:
    base = {
        "numero": "01/2026/DGC/SUPGES",
        "fornecedor": "Empresa Alfa",
        "setor": "DGC",
        "inicio": "2026-01-01",
        "fim": "2026-12-31",
        "valor": 1000,
        "pago": 100,
        "objeto": "Suporte de sistemas",
        "fiscal": "Ana Fiscal",
        "gestor": "Bruno Gestor",
        "diaPagamento": 10,
        "renovavel": True,
        "processo": "2026/1/1",
        "modalidade": "Pregão Eletrônico",
    }
    base.update(extras)
    return base


def plantar(raiz: Path, superintendencia: str, pasta: str, dados: dict) -> Path:
    destino = raiz / superintendencia / pasta
    destino.mkdir(parents=True)
    (destino / "contrato.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return destino


def config_de(raiz: Path, senha: str = "segredo") -> dict:
    return {
        "orgao": "ATI",
        "orgaoNome": "Agência de Tecnologia da Informação do Tocantins",
        "usuario": {"nome": "Usuária Teste", "cargo": "Fiscal"},
        "dadosIlustrativos": False,
        "raizArquivos": str(raiz),
        "regras": {"janelaRenovacaoDias": 120, "limiteExecucao": 0.85},
        "modulos": [{"id": "contratos", "nome": "Contratos", "ativo": True}],
        "acesso": {"usuario": "admin", "senha": hash_senha(senha)},
    }


class Cliente:
    """Navegador mínimo: guarda o cookie e não segue redirecionamento."""

    def __init__(self, porta: int) -> None:
        self.porta = porta
        self.cookie = ""

    def pedir(self, metodo: str, caminho: str, corpo: dict | list | str | None = None, bruto: bytes | None = None):
        import http.client

        conn = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=30)
        cabecalhos = {}
        if self.cookie:
            cabecalhos["Cookie"] = self.cookie
        dados = bruto
        if corpo is not None:
            dados = json.dumps(corpo).encode("utf-8")
            cabecalhos["Content-Type"] = "application/json"
        if dados is not None:
            cabecalhos["Content-Length"] = str(len(dados))
        conn.request(metodo, caminho, body=dados, headers=cabecalhos)
        resposta = conn.getresponse()
        conteudo = resposta.read()
        cookie = resposta.getheader("Set-Cookie") or ""
        if "Max-Age=0" in cookie:
            self.cookie = ""
        elif cookie.startswith("sessao="):
            self.cookie = cookie.split(";", 1)[0]
        conn.close()
        return resposta.status, resposta.getheader("Location") or "", conteudo, cookie


@contextmanager
def servidor_de_teste(raiz: Path, senha: str = "segredo"):
    manipulador = fabricar_manipulador(config_de(raiz, senha), ServicoSessao())
    manipulador.log_message = lambda self, formato, *args: None
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), manipulador)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield Cliente(httpd.server_address[1])
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
