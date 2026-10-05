"""Regras de aceitação de um contrato."""

from __future__ import annotations

import unittest
from pathlib import Path

from app.dominio.contrato import validar
from testes.apoio import contrato


class ValidacaoDeContrato(unittest.TestCase):
    def setUp(self) -> None:
        self.pasta = Path("SUPGES") / "alfa"
        self.vistos: set[tuple[str, str]] = set()

    def test_aceita_contrato_completo_e_normaliza(self) -> None:
        item, erro = validar(contrato(valor="1250.50", pago=None, fiscal=None, diaPagamento=""), "SUPGES", self.pasta, self.vistos)
        self.assertIsNone(erro)
        assert item is not None
        self.assertEqual(item["id"], "SUPGES/01/2026/DGC/SUPGES")
        self.assertEqual(item["valor"], 1250.50)
        self.assertEqual(item["pago"], 0.0)
        self.assertEqual(item["fiscal"], "")
        self.assertIsNone(item["diaPagamento"])
        self.assertTrue(item["renovavel"])
        self.assertEqual(item["pasta"], str(self.pasta))

    def test_usa_nome_da_pasta_quando_falta_numero(self) -> None:
        dados = contrato()
        dados.pop("numero")
        item, erro = validar(dados, "SUPGES", self.pasta, self.vistos)
        self.assertIsNone(erro)
        assert item is not None
        self.assertEqual(item["numero"], "alfa")

    def test_rejeita_campo_obrigatorio_vazio(self) -> None:
        item, erro = validar(contrato(fornecedor=""), "SUPGES", self.pasta, self.vistos)
        self.assertIsNone(item)
        assert erro is not None
        self.assertIn("fornecedor", erro["faltando"])

    def test_rejeita_data_fora_do_padrao(self) -> None:
        item, erro = validar(contrato(fim="22/04/2026", assinatura="abril"), "SUPGES", self.pasta, self.vistos)
        self.assertIsNone(item)
        assert erro is not None
        self.assertIn("fim (use AAAA-MM-DD)", erro["faltando"])
        self.assertIn("assinatura (use AAAA-MM-DD)", erro["faltando"])

    def test_rejeita_numero_duplicado_na_mesma_superintendencia(self) -> None:
        validar(contrato(), "SUPGES", self.pasta, self.vistos)
        item, erro = validar(contrato(), "SUPGES", self.pasta, self.vistos)
        self.assertIsNone(item)
        assert erro is not None
        self.assertIn("numero duplicado na superintendência", erro["faltando"])

    def test_mesmo_numero_em_outra_superintendencia_passa(self) -> None:
        validar(contrato(), "SUPGES", self.pasta, self.vistos)
        item, erro = validar(contrato(), "SUPSIS", Path("SUPSIS") / "alfa", self.vistos)
        self.assertIsNone(erro)
        self.assertIsNotNone(item)

    def test_rejeita_item_que_nao_e_objeto(self) -> None:
        item, erro = validar(["lista"], "SUPGES", self.pasta, self.vistos)  # type: ignore[arg-type]
        self.assertIsNone(item)
        assert erro is not None
        self.assertEqual(erro["faltando"], ["objeto"])


if __name__ == "__main__":
    unittest.main()
