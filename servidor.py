"""Servidor local da visão de contratos da ATI.

Le config.json, garante a pasta do servidor de arquivos e entrega
os contratos de <raizArquivos>/contratos.json para a tela.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OBRIGATORIOS = ("numero", "fornecedor", "setor", "inicio", "fim", "valor")


def caminho(valor: str) -> Path:
    bruto = Path(valor)
    if bruto.is_absolute():
        return bruto
    return ROOT / bruto


def ler_config() -> dict:
    with (ROOT / "config.json").open(encoding="utf-8-sig") as arquivo:
        config = json.load(arquivo)
    if "raizArquivos" not in config:
        raise SystemExit("config.json precisa do campo raizArquivos.")
    config.setdefault("orgao", "ATI")
    config.setdefault("host", "127.0.0.1")
    config.setdefault("porta", 8765)
    config.setdefault("dadosIlustrativos", False)
    config.setdefault("regras", {})
    config["regras"].setdefault("janelaRenovacaoDias", 120)
    config["regras"].setdefault("limiteExecucao", 0.85)
    config.setdefault("andares", {})
    config.setdefault("modulos", [])
    return config


def garantir_pastas(config: dict) -> list[dict]:
    raiz = caminho(config["raizArquivos"])
    criadas = []
    alvos = [raiz]
    for andar, pastas in config["andares"].items():
        for nome in pastas:
            pasta = raiz / andar / nome
            alvos.append(pasta)
            if nome == "contratos":
                alvos.append(pasta / "por_fornecedor")
    for pasta in alvos:
        pasta.mkdir(parents=True, exist_ok=True)
        criadas.append({"caminho": str(pasta), "existe": pasta.is_dir()})
    return criadas


def carregar_contratos(config: dict) -> tuple[list[dict], list[dict], Path]:
    registro = caminho(config["raizArquivos"]) / "contratos.json"
    if not registro.exists():
        registro.write_text("[]\n", encoding="utf-8")
        return [], [], registro

    with registro.open(encoding="utf-8-sig") as arquivo:
        bruto = json.load(arquivo)
    if isinstance(bruto, dict):
        bruto = bruto.get("contratos", [])
    if not isinstance(bruto, list):
        return [], [{"numero": "", "faltando": ["lista de contratos"]}], registro

    validos = []
    erros = []
    vistos = set()
    for indice, item in enumerate(bruto, start=1):
        if not isinstance(item, dict):
            erros.append({"linha": indice, "numero": "", "faltando": ["objeto"]})
            continue
        numero = str(item.get("numero") or "").strip()
        faltando = [campo for campo in OBRIGATORIOS if item.get(campo) in (None, "")]
        for campo in ("inicio", "fim", "assinatura"):
            valor = item.get(campo)
            if valor and not DATA_RE.match(str(valor)):
                faltando.append(campo + " (use AAAA-MM-DD)")
        if numero and numero in vistos:
            faltando.append("numero duplicado")
        if faltando:
            erros.append({"linha": indice, "numero": numero, "faltando": faltando})
            continue
        contrato = dict(item)
        contrato["numero"] = numero
        contrato["valor"] = float(contrato["valor"])
        contrato["pago"] = float(contrato.get("pago") or 0)
        dia = contrato.get("diaPagamento")
        contrato["diaPagamento"] = None if dia in (None, "") else int(dia)
        contrato["renovavel"] = bool(contrato.get("renovavel"))
        for campo in ("fiscal", "gestor", "objeto", "processo", "modalidade", "fonte", "programa", "nd", "fornecedor", "setor"):
            if contrato.get(campo) is None:
                contrato[campo] = ""
        vistos.add(numero)
        validos.append(contrato)
    return validos, erros, registro


def painel(config: dict) -> dict:
    contratos, erros, registro = carregar_contratos(config)
    return {
        "orgao": config["orgao"],
        "ilustrativo": bool(config.get("dadosIlustrativos")),
        "registro": str(registro),
        "raizArquivos": str(caminho(config["raizArquivos"])),
        "regras": {
            "janelaRenovacaoDias": int(config["regras"]["janelaRenovacaoDias"]),
            "limiteExecucao": float(config["regras"]["limiteExecucao"]),
        },
        "modulos": config["modulos"],
        "pastas": garantir_pastas(config),
        "contratos": contratos,
        "erros": erros,
    }


class Aplicacao(BaseHTTPRequestHandler):
    config: dict = {}

    def log_message(self, formato: str, *args) -> None:
        if args and str(args[0]).startswith("GET /favicon"):
            return
        super().log_message(formato, *args)

    def do_GET(self) -> None:
        rota = self.path.split("?", 1)[0]
        if rota == "/api/contratos":
            corpo = json.dumps(painel(self.config), ensure_ascii=False).encode("utf-8")
            self._enviar(200, "application/json; charset=utf-8", corpo)
            return
        if rota in ("/", "/contratos", "/contratos.html"):
            html = (ROOT / "contratos.html").read_bytes()
            self._enviar(200, "text/html; charset=utf-8", html)
            return
        self.send_error(404)

    def _enviar(self, status: int, tipo: str, corpo: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)


def main() -> None:
    config = ler_config()
    Aplicacao.config = config
    pastas = garantir_pastas(config)
    host = str(config["host"])
    porta = int(config["porta"])
    try:
        servidor = ThreadingHTTPServer((host, porta), Aplicacao)
    except OSError as erro:
        raise SystemExit(f"Não foi possível abrir {host}:{porta}. {erro}") from erro
    print(f"{config['orgao']} · gestão de contratos", flush=True)
    print(f"Abra http://{host}:{porta}/", flush=True)
    print(f"Registro: {caminho(config['raizArquivos']) / 'contratos.json'}", flush=True)
    print(f"Pastas prontas: {len(pastas)}", flush=True)
    if config.get("dadosIlustrativos"):
        print("Base ilustrativa. Para a base real, troque raizArquivos e marque dadosIlustrativos como false.", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")


if __name__ == "__main__":
    main()
