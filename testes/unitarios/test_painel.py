"""Painel entregue às telas e proteção dos arquivos estáticos."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.aplicacao.painel import montar_painel
from app.apresentacao.http import arquivo_web
from app.infraestrutura.caminhos import RAIZ
from testes.apoio import config_de, contrato, plantar


class Painel(unittest.TestCase):
    def test_monta_cabecalho_regras_e_contratos(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            plantar(raiz, "SUPGES", "alfa", contrato())
            painel = montar_painel(config_de(raiz))
            self.assertEqual(painel["orgao"], "ATI")
            self.assertEqual(painel["usuario"]["nome"], "Usuária Teste")
            self.assertEqual(painel["regras"]["janelaRenovacaoDias"], 120)
            self.assertEqual(painel["regras"]["limiteExecucao"], 0.85)
            self.assertEqual(len(painel["contratos"]), 1)
            self.assertNotIn("senha", json.dumps(painel))

    def test_arquivo_web_fica_dentro_da_pasta_publica(self) -> None:
        css = arquivo_web("/web/paginas/login/login.css")
        self.assertIsNotNone(css)
        assert css is not None
        self.assertTrue(css.is_file())
        self.assertIsNone(arquivo_web("/web/../config.json"))
        self.assertIsNone(arquivo_web("/web/paginas/login/../../../config.json"))
        self.assertIsNone(arquivo_web("/api/contratos"))
        self.assertFalse((RAIZ / "config.json").resolve() == (css.resolve()))


if __name__ == "__main__":
    unittest.main()
