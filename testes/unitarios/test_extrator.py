"""Leitura do termo: texto sintético, escolha do PDF e o contrato MSB."""

from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from app.infraestrutura.caminhos import RAIZ
from app.infraestrutura.extrator_pdf import dinheiro, extrair_arquivo, extrair_texto, pdf_do_contrato, somar_meses

TEXTO = """
TERMO DE CONTRATO N. 07/2025/DGC/SUPGES/ATI
PROCESSO N. 2023/26810/000052
empresa MSB TECNOLOGIA LTDA, pessoa jurídica de direito privado
CLÁUSULA PRIMEIRA - DO OBJETO O presente contrato tem por objeto a contratação de fábrica de software PARÁGRAFO ÚNICO
Pregão Eletrônico
Aos 23 dias do mês de abril de 2025
vigência de 12 (doze) meses, podendo ser prorrogado
valor do presente Termo de Contrato é de R$ 16.750.000,00
Função: 4
Subfunção: 126
Programa: 1166
Fonte: 500
Natureza: 33.90.40
"""


class Extrator(unittest.TestCase):
    def test_dinheiro_e_vigencia(self) -> None:
        self.assertEqual(dinheiro("16.750.000,00"), 16750000.0)
        self.assertEqual(somar_meses(date(2025, 4, 23), 12), date(2026, 4, 22))
        self.assertEqual(somar_meses(date(2024, 1, 31), 1), date(2024, 2, 28))

    def test_extrai_campos_do_texto_do_termo(self) -> None:
        item = extrair_texto(TEXTO, "termo.pdf")
        self.assertEqual(item["numero"], "07/2025/DGC/SUPGES/ATI")
        self.assertEqual(item["fornecedor"], "MSB TECNOLOGIA LTDA")
        self.assertEqual(item["setor"], "DGC")
        self.assertEqual(item["superintendencia"], "SUPGES")
        self.assertEqual(item["processo"], "2023/26810/000052")
        self.assertEqual(item["modalidade"], "Pregão Eletrônico")
        self.assertEqual(item["inicio"], "2025-04-23")
        self.assertEqual(item["fim"], "2026-04-22")
        self.assertEqual(item["valor"], 16750000.0)
        self.assertEqual(item["programa"], "04.126.1166")
        self.assertEqual(item["fonte"], "500")
        self.assertEqual(item["nd"], "33.90.40")
        self.assertTrue(item["renovavel"])
        self.assertTrue(item["objeto"].startswith("Contratação"))

    def test_prefere_pdf_com_contrato_no_nome(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta)
            (base / "anexo.pdf").write_bytes(b"%PDF")
            escolhido = base / "Contrato MSB.pdf"
            escolhido.write_bytes(b"%PDF")
            self.assertEqual(pdf_do_contrato(base), escolhido)
            self.assertIsNone(pdf_do_contrato(base / "vazia"))

    def test_pdf_msb_gera_o_mesmo_indice(self) -> None:
        pdf = RAIZ / "arquivos_base" / "Contrato MSB.pdf"
        if not pdf.is_file():
            self.skipTest("PDF de exemplo ausente")
        item = extrair_arquivo(pdf)
        self.assertEqual(item["numero"], "07/2025/DGC/SUPGES/ATI")
        self.assertEqual(item["fornecedor"], "MSB TECNOLOGIA LTDA")
        self.assertEqual(item["valor"], 16750000.0)
        self.assertEqual(item["fim"], "2026-04-22")
        self.assertEqual(item["arquivo"], "Contrato MSB.pdf")


if __name__ == "__main__":
    unittest.main()
