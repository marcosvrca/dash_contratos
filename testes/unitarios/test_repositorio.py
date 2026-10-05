"""Leitura da árvore de pastas de contratos."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.infraestrutura.repositorio_contratos import carregar
from testes.apoio import contrato, plantar


class Repositorio(unittest.TestCase):
    def test_carrega_contrato_valido(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            plantar(raiz, "SUPGES", "alfa", contrato())
            validos, erros, registro, pastas = carregar({"raizArquivos": str(raiz)})
            self.assertEqual(registro, raiz)
            self.assertEqual(erros, [])
            self.assertEqual(len(validos), 1)
            self.assertEqual(validos[0]["id"], "SUPGES/01/2026/DGC/SUPGES")
            self.assertEqual([p["tipo"] for p in pastas], ["raiz", "superintendencia", "contrato"])

    def test_separa_incompleto_duplicado_e_json_ilegivel(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            plantar(raiz, "SUPGES", "alfa", contrato())
            plantar(raiz, "SUPGES", "copia", contrato())
            plantar(raiz, "SUPGES", "sem-valor", contrato(valor=None))
            ruim = raiz / "SUPSIS" / "quebrado"
            ruim.mkdir(parents=True)
            (ruim / "contrato.json").write_text("{nao e json", encoding="utf-8")
            validos, erros, _, _ = carregar({"raizArquivos": str(raiz)})
            self.assertEqual(len(validos), 1)
            textos = " ".join(" ".join(e["faltando"]) for e in erros)
            self.assertIn("duplicado", textos)
            self.assertIn("valor", textos)
            self.assertIn("ilegível", textos)

    def test_pasta_inexistente_arquivo_e_superintendencia_vazia(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            validos, erros, _, _ = carregar({"raizArquivos": str(raiz / "nao-existe")})
            self.assertEqual(validos, [])
            self.assertIn("indisponível", erros[0]["faltando"][0])

            arquivo = raiz / "nao-e-pasta.txt"
            arquivo.write_text("x", encoding="utf-8")
            _, erros, _, _ = carregar({"raizArquivos": str(arquivo)})
            self.assertIn("não é uma pasta", erros[0]["faltando"][0])

            (raiz / "ociosa").mkdir()
            _, erros, _, pastas = carregar({"raizArquivos": str(raiz / "ociosa")})
            self.assertIn("nenhuma pasta de superintendência", erros[0]["faltando"][0])
            self.assertEqual(pastas[0]["tipo"], "raiz")

            (raiz / "SUPGES").mkdir()
            _, erros, _, _ = carregar({"raizArquivos": str(raiz)})
            self.assertTrue(any("nenhuma pasta de contrato" in " ".join(e["faltando"]) for e in erros))

    def test_pdf_sem_json_grava_o_indice(self) -> None:
        origem = Path(__file__).resolve().parents[2] / "arquivos_base" / "Contrato MSB.pdf"
        if not origem.is_file():
            self.skipTest("PDF de exemplo ausente")
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            destino = raiz / "SUPGES" / "msb"
            destino.mkdir(parents=True)
            (destino / "Contrato MSB.pdf").write_bytes(origem.read_bytes())
            validos, erros, _, _ = carregar({"raizArquivos": str(raiz)})
            self.assertEqual(erros, [])
            self.assertEqual(validos[0]["numero"], "07/2025/DGC/SUPGES/ATI")
            gravado = json.loads((destino / "contrato.json").read_text(encoding="utf-8"))
            self.assertEqual(gravado["fornecedor"], "MSB TECNOLOGIA LTDA")


if __name__ == "__main__":
    unittest.main()
