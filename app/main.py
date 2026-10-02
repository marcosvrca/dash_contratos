"""Composição da aplicação e arranque do servidor."""

from __future__ import annotations

from app.aplicacao.sessao import ServicoSessao
from app.apresentacao.http import servir
from app.infraestrutura.configuracao import ler, preparar_acesso


def main() -> None:
    config = ler()
    senha_nova = preparar_acesso(config)
    if senha_nova:
        config["_senha_inicial"] = senha_nova
    servir(config, ServicoSessao())


if __name__ == "__main__":
    main()
