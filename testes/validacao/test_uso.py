"""Simula a visita de quem usa o sistema: login, painel, contratos e saída."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from testes.apoio import contrato, plantar, servidor_de_teste


class UsoDoUsuario(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)
        plantar(self.raiz, "SUPGES", "alfa", contrato())
        plantar(self.raiz, "SUPSIS", "sem-fornecedor", contrato(numero="02/2026/SIS/SUPSIS", fornecedor=""))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sem_sessao_o_painel_fica_no_login(self) -> None:
        with servidor_de_teste(self.raiz) as cliente:
            status, destino, corpo, _ = cliente.pedir("GET", "/")
            self.assertEqual(status, 302)
            self.assertTrue(destino.startswith("/login?next=/"))
            status, _, corpo, _ = cliente.pedir("GET", "/login")
            pagina = corpo.decode("utf-8")
            self.assertEqual(status, 200)
            self.assertIn("Acesso restrito", pagina)
            self.assertIn('id="usuario"', pagina)
            self.assertIn('id="senha"', pagina)
            self.assertIn("login.viewmodel.js", pagina)
            status, _, corpo, _ = cliente.pedir("GET", "/api/contratos")
            self.assertEqual(status, 401)
            status, _, css, _ = cliente.pedir("GET", "/web/paginas/login/login.css")
            self.assertEqual(status, 200)
            self.assertIn("font-family", css.decode("utf-8"))
            status, _, _, _ = cliente.pedir("GET", "/web/paginas/dashboard/dashboard.css")
            self.assertEqual(status, 401)

    def test_senha_errada_nao_abre_o_sistema(self) -> None:
        with servidor_de_teste(self.raiz) as cliente:
            status, _, corpo, cookie = cliente.pedir("POST", "/api/entrar", {"usuario": "admin", "senha": "errada"})
            self.assertEqual(status, 401)
            self.assertIn("incorretos", json.loads(corpo)["erro"])
            self.assertNotIn("sessao=", cookie)
            status, _, _, _ = cliente.pedir("GET", "/api/contratos")
            self.assertEqual(status, 401)

    def test_entra_consulta_a_carteira_e_sai(self) -> None:
        with servidor_de_teste(self.raiz) as cliente:
            status, _, corpo, cookie = cliente.pedir("POST", "/api/entrar", {"usuario": "admin", "senha": "segredo"})
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(corpo)["ok"])
            self.assertIn("HttpOnly", cookie)
            self.assertIn("SameSite=Lax", cookie)

            status, destino, pagina, _ = cliente.pedir("GET", "/login")
            self.assertEqual(status, 302)
            self.assertEqual(destino, "/")

            status, _, pagina, _ = cliente.pedir("GET", "/")
            html = pagina.decode("utf-8")
            self.assertEqual(status, 200)
            self.assertIn('id="kpis"', html)
            self.assertIn('id="q"', html)
            self.assertIn('id="periodo"', html)
            self.assertIn('id="sair"', html)
            self.assertIn("dashboard.viewmodel.js", html)

            status, _, corpo, _ = cliente.pedir("GET", "/api/contratos")
            painel = json.loads(corpo)
            self.assertEqual(status, 200)
            self.assertEqual(painel["usuario"], {"nome": "Usuária Teste", "cargo": "Fiscal"})
            self.assertEqual(painel["regras"]["janelaRenovacaoDias"], 120)
            self.assertEqual(len(painel["contratos"]), 1)
            self.assertEqual(painel["contratos"][0]["fornecedor"], "Empresa Alfa")
            self.assertTrue(painel["erros"])
            self.assertNotIn("senha", json.dumps(painel))

            status, _, pagina, _ = cliente.pedir("GET", "/contratos")
            html = pagina.decode("utf-8")
            self.assertEqual(status, 200)
            self.assertIn('id="tbl"', html)
            self.assertIn('id="fsup"', html)
            self.assertIn('id="dlg"', html)
            self.assertIn("contratos.viewmodel.js", html)

            status, _, script, _ = cliente.pedir("GET", "/web/paginas/contratos/contratos.model.js")
            self.assertEqual(status, 200)
            self.assertIn("export function lista", script.decode("utf-8"))

            status, _, corpo, cookie = cliente.pedir("POST", "/api/sair")
            self.assertEqual(status, 200)
            self.assertIn("Max-Age=0", cookie)
            status, destino, _, _ = cliente.pedir("GET", "/")
            self.assertEqual(status, 302)
            self.assertTrue(destino.startswith("/login"))

    def test_cinco_erros_seguidos_bloqueiam_o_acesso(self) -> None:
        with servidor_de_teste(self.raiz) as cliente:
            for _ in range(5):
                status, _, _, _ = cliente.pedir("POST", "/api/entrar", {"usuario": "admin", "senha": "errada"})
                self.assertEqual(status, 401)
            status, _, corpo, _ = cliente.pedir("POST", "/api/entrar", {"usuario": "admin", "senha": "segredo"})
            self.assertEqual(status, 429)
            self.assertIn("Aguarde", json.loads(corpo)["erro"])

    def test_pedido_invalido_e_rota_desconhecida(self) -> None:
        with servidor_de_teste(self.raiz) as cliente:
            status, _, corpo, _ = cliente.pedir("POST", "/api/entrar")
            self.assertEqual(status, 400)
            status, _, _, _ = cliente.pedir("POST", "/api/entrar", bruto=b"nao-json")
            self.assertEqual(status, 400)
            status, _, _, _ = cliente.pedir("POST", "/api/entrar", bruto=b'{"usuario":"a"}' + b" " * 2100)
            self.assertEqual(status, 400)
            cliente.pedir("POST", "/api/entrar", {"usuario": "admin", "senha": "segredo"})
            status, _, _, _ = cliente.pedir("GET", "/nao-existe")
            self.assertEqual(status, 404)
            status, _, _, _ = cliente.pedir("POST", "/api/outra")
            self.assertEqual(status, 404)
            status, destino, corpo, _ = cliente.pedir("GET", "/web/../config.json")
            self.assertNotIn(b"pbkdf2", corpo)
            self.assertNotEqual(status, 200)

    def test_configuracao_do_projeto_tem_o_que_o_servidor_exige(self) -> None:
        from app.infraestrutura.caminhos import RAIZ

        config = json.loads((RAIZ / "config.json").read_text(encoding="utf-8-sig"))
        self.assertIn("raizArquivos", config)
        self.assertIn("orgao", config)
        self.assertIn("regras", config)
        self.assertGreater(config["regras"]["janelaRenovacaoDias"], 0)
        self.assertGreater(config["regras"]["limiteExecucao"], 0)
        self.assertTrue(config["acesso"]["usuario"])
        self.assertTrue(str(config["acesso"]["senha"]).startswith("pbkdf2$"))


if __name__ == "__main__":
    unittest.main()
