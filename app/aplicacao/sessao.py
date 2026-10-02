"""Caso de uso de sessão: entrada, saída e cookie."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from app.infraestrutura.senha import senha_confere

SESSAO_SEGUNDOS = 8 * 60 * 60
FALHAS_MAX = 5
FALHAS_JANELA = 15 * 60


class ServicoSessao:
    def __init__(self) -> None:
        self._sessoes: dict[str, float] = {}
        self._falhas: dict[str, list[float]] = {}

    def bloqueado(self, ip: str, agora: float | None = None) -> bool:
        agora = time.time() if agora is None else agora
        recentes = [t for t in self._falhas.get(ip, []) if agora - t < FALHAS_JANELA]
        self._falhas[ip] = recentes
        return len(recentes) >= FALHAS_MAX

    def entrar(self, config: dict, usuario: str, senha: str, ip: str) -> tuple[int, str, str | None]:
        agora = time.time()
        if self.bloqueado(ip, agora):
            return 429, "Muitas tentativas. Aguarde alguns minutos.", None
        acesso = config.get("acesso") or {}
        esperado = str(acesso.get("usuario") or "")
        usuario_ok = hmac.compare_digest(
            hashlib.sha256(usuario.encode("utf-8")).digest(),
            hashlib.sha256(esperado.encode("utf-8")).digest(),
        )
        if not usuario_ok or not senha_confere(senha, str(acesso.get("senha") or "")):
            self._falhas.setdefault(ip, []).append(agora)
            return 401, "Usuário ou senha incorretos.", None
        self._falhas.pop(ip, None)
        token = secrets.token_urlsafe(32)
        self._sessoes[token] = agora + SESSAO_SEGUNDOS
        cookie = f"sessao={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSAO_SEGUNDOS}"
        return 200, "", cookie

    def sair(self, token: str) -> str:
        if token:
            self._sessoes.pop(token, None)
        return "sessao=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"

    def autenticado(self, token: str) -> bool:
        if not token:
            return False
        expira = self._sessoes.get(token)
        if not expira or expira < time.time():
            self._sessoes.pop(token, None)
            return False
        return True
