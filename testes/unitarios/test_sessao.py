"""Entrada, bloqueio e expiração da sessão."""

from __future__ import annotations

import time
import unittest

from app.aplicacao.sessao import FALHAS_JANELA, FALHAS_MAX, ServicoSessao
from app.infraestrutura.senha import hash_senha


class Sessao(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.senha = hash_senha("segredo")
        cls.config = {"acesso": {"usuario": "admin", "senha": cls.senha}}

    def setUp(self) -> None:
        self.sessao = ServicoSessao()

    def test_entra_e_reconhece_o_token(self) -> None:
        status, mensagem, cookie = self.sessao.entrar(self.config, "admin", "segredo", "10.0.0.1")
        self.assertEqual(status, 200)
        self.assertEqual(mensagem, "")
        assert cookie is not None
        self.assertIn("HttpOnly", cookie)
        token = cookie.split(";", 1)[0].split("=", 1)[1]
        self.assertTrue(self.sessao.autenticado(token))

    def test_rejeita_senha_e_usuario_errados(self) -> None:
        status, mensagem, cookie = self.sessao.entrar(self.config, "admin", "errada", "10.0.0.2")
        self.assertEqual((status, cookie), (401, None))
        self.assertIn("incorretos", mensagem)
        status, _, _ = self.sessao.entrar(self.config, "intruso", "segredo", "10.0.0.3")
        self.assertEqual(status, 401)

    def test_bloqueia_depois_de_cinco_falhas_e_esquece_ao_acertar(self) -> None:
        for _ in range(FALHAS_MAX):
            status, _, _ = self.sessao.entrar(self.config, "admin", "errada", "10.0.0.4")
            self.assertEqual(status, 401)
        status, mensagem, _ = self.sessao.entrar(self.config, "admin", "segredo", "10.0.0.4")
        self.assertEqual(status, 429)
        self.assertIn("Aguarde", mensagem)
        self.sessao._falhas["10.0.0.4"] = [time.time() - FALHAS_JANELA - 5] * FALHAS_MAX
        status, _, cookie = self.sessao.entrar(self.config, "admin", "segredo", "10.0.0.4")
        self.assertEqual(status, 200)
        self.assertIsNotNone(cookie)

    def test_sessao_vencida_e_saida_invalidam_o_token(self) -> None:
        _, _, cookie = self.sessao.entrar(self.config, "admin", "segredo", "10.0.0.5")
        assert cookie is not None
        token = cookie.split(";", 1)[0].split("=", 1)[1]
        self.sessao._sessoes[token] = time.time() - 1
        self.assertFalse(self.sessao.autenticado(token))
        _, _, cookie = self.sessao.entrar(self.config, "admin", "segredo", "10.0.0.5")
        assert cookie is not None
        token = cookie.split(";", 1)[0].split("=", 1)[1]
        self.sessao.sair(token)
        self.assertFalse(self.sessao.autenticado(token))
        self.assertFalse(self.sessao.autenticado(""))


if __name__ == "__main__":
    unittest.main()
