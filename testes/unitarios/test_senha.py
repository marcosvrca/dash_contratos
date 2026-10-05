"""Hash de senha."""

from __future__ import annotations

import unittest

from app.infraestrutura.senha import hash_senha, senha_confere


class Senha(unittest.TestCase):
    def test_confere_a_senha_gravada(self) -> None:
        gravada = hash_senha("segredo")
        self.assertTrue(senha_confere("segredo", gravada))
        self.assertFalse(senha_confere("outra", gravada))

    def test_dois_hashes_da_mesma_senha_diferem(self) -> None:
        self.assertNotEqual(hash_senha("segredo"), hash_senha("segredo"))

    def test_rejeita_formato_invalido(self) -> None:
        self.assertFalse(senha_confere("segredo", ""))
        self.assertFalse(senha_confere("segredo", "texto-puro"))
        self.assertFalse(senha_confere("segredo", "pbkdf2$zz$yy"))


if __name__ == "__main__":
    unittest.main()
