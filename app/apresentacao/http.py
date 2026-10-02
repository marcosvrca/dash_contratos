"""Manipulador HTTP. A regra de negócio fica nos casos de uso."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from app.aplicacao.painel import montar_painel
from app.aplicacao.sessao import ServicoSessao
from app.dominio.contrato import ARQUIVO_CONTRATO
from app.infraestrutura.caminhos import RAIZ, caminho

WEB = RAIZ / "web"
PAGINAS = {
    "/": "paginas/dashboard/dashboard.html",
    "/dashboard": "paginas/dashboard/dashboard.html",
    "/dashboard.html": "paginas/dashboard/dashboard.html",
    "/contratos": "paginas/contratos/contratos.html",
    "/contratos.html": "paginas/contratos/contratos.html",
}
LOGIN = "paginas/login/login.html"
TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}
PUBLICO = ("/web/paginas/login/", "/web/compartilhados/")


def arquivo_web(rota: str) -> Path | None:
    if not rota.startswith("/web/"):
        return None
    relativo = unquote(rota[len("/web/"):])
    if not relativo or relativo.startswith(("/", "\\")) or "\\" in relativo:
        return None
    base = WEB.resolve()
    destino = (base / relativo).resolve()
    try:
        destino.relative_to(base)
    except ValueError:
        return None
    if destino.is_file():
        return destino
    return None


def fabricar_manipulador(config: dict, sessao: ServicoSessao):
    class Manipulador(BaseHTTPRequestHandler):
        def log_message(self, formato: str, *args) -> None:
            if args and str(args[0]).startswith("GET /favicon"):
                return
            super().log_message(formato, *args)

        def do_GET(self) -> None:
            rota = urlparse(self.path).path
            if rota == "/favicon.ico":
                self.send_error(404)
                return
            estatico = arquivo_web(rota)
            if estatico is not None:
                if not _rota_publica(rota) and not self._autenticado():
                    self._enviar(401, "application/json; charset=utf-8", b'{"erro":"acesso negado"}')
                    return
                tipo = TIPOS.get(estatico.suffix.lower(), "application/octet-stream")
                self._enviar(200, tipo, estatico.read_bytes())
                return
            if rota in ("/login", "/login.html"):
                if self._autenticado():
                    self._redirecionar("/")
                    return
                self._enviar(200, "text/html; charset=utf-8", (WEB / LOGIN).read_bytes())
                return
            if not self._autenticado():
                if rota.startswith("/api/"):
                    self._enviar(401, "application/json; charset=utf-8", b'{"erro":"acesso negado"}')
                    return
                destino = rota if rota.startswith("/") and not rota.startswith("//") else "/"
                self._redirecionar("/login?next=" + quote(destino, safe="/"))
                return
            if rota == "/api/contratos":
                corpo = json.dumps(montar_painel(config), ensure_ascii=False).encode("utf-8")
                self._enviar(200, "application/json; charset=utf-8", corpo)
                return
            pagina = PAGINAS.get(rota)
            if pagina:
                self._enviar(200, "text/html; charset=utf-8", (WEB / pagina).read_bytes())
                return
            self.send_error(404)

        def do_POST(self) -> None:
            rota = urlparse(self.path).path
            if rota == "/api/entrar":
                self._entrar()
                return
            if rota == "/api/sair":
                self._sair()
                return
            self.send_error(404)

        def _entrar(self) -> None:
            ip = self.client_address[0]
            if sessao.bloqueado(ip):
                self._json(429, {"erro": "Muitas tentativas. Aguarde alguns minutos."})
                return
            corpo = self._ler_json()
            if corpo is None:
                self._json(400, {"erro": "Pedido inválido."})
                return
            status, mensagem, cookie = sessao.entrar(
                config,
                str(corpo.get("usuario") or ""),
                str(corpo.get("senha") or ""),
                ip,
            )
            if status != 200:
                self._json(status, {"erro": mensagem})
                return
            self._json(200, {"ok": True}, cookie=cookie)

        def _sair(self) -> None:
            cookie = sessao.sair(self._cookie("sessao"))
            self._json(200, {"ok": True}, cookie=cookie)

        def _autenticado(self) -> bool:
            return sessao.autenticado(self._cookie("sessao"))

        def _cookie(self, nome: str) -> str:
            bruto = self.headers.get("Cookie", "")
            for parte in bruto.split(";"):
                chave, _, valor = parte.strip().partition("=")
                if chave == nome:
                    return valor
            return ""

        def _ler_json(self) -> dict | None:
            try:
                tamanho = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return None
            if tamanho <= 0 or tamanho > 2048:
                return None
            try:
                dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None
            return dados if isinstance(dados, dict) else None

        def _json(self, status: int, dados: dict, cookie: str | None = None) -> None:
            extra = {"Set-Cookie": cookie} if cookie else None
            self._enviar(status, "application/json; charset=utf-8", json.dumps(dados).encode("utf-8"), extra)

        def _redirecionar(self, destino: str) -> None:
            self.send_response(302)
            self.send_header("Location", destino)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _enviar(self, status: int, tipo: str, corpo: bytes, extra: dict | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for chave, valor in (extra or {}).items():
                self.send_header(chave, valor)
            self.end_headers()
            self.wfile.write(corpo)

    return Manipulador


def _rota_publica(rota: str) -> bool:
    return rota.startswith(PUBLICO)


def servir(config: dict, sessao: ServicoSessao) -> None:
    host = str(config["host"])
    porta = int(config["porta"])
    try:
        servidor = ThreadingHTTPServer((host, porta), fabricar_manipulador(config, sessao))
    except OSError as erro:
        raise SystemExit(f"Não foi possível abrir {host}:{porta}. {erro}") from erro
    raiz = caminho(config["raizArquivos"])
    print(f"{config['orgao']} · gestão de contratos", flush=True)
    print(f"Abra http://{host}:{porta}/", flush=True)
    print(f"Contratos: {raiz}\\<superintendência>\\<contrato>\\{ARQUIVO_CONTRATO}", flush=True)
    print(f"Acesso restrito. Usuário: {config['acesso']['usuario']}", flush=True)
    if config.get("_senha_inicial"):
        print(f"Senha inicial: {config['_senha_inicial']}", flush=True)
        print("Guarde esta senha. Ela não será mostrada de novo.", flush=True)
        print("Para trocar, coloque a nova senha em config.json, no campo acesso.senha, e reinicie.", flush=True)
    if config.get("dadosIlustrativos"):
        print("Base ilustrativa. Para a base real, troque raizArquivos e marque dadosIlustrativos como false.", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
