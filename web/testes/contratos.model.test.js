import assert from "node:assert/strict";
import test from "node:test";

import { dayMs, hoje } from "../compartilhados/formatacao.js";
import { alertas, lista, ordenar, proximoPagamento, saldo, situacao } from "../paginas/contratos/contratos.model.js";

function iso(data) {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function deslocar(dias) {
  return iso(new Date(hoje.getTime() + dias * dayMs));
}

function contrato(parcial) {
  return {
    numero: "01/2026",
    superintendencia: "SUPGES",
    fornecedor: "Empresa Alfa",
    objeto: "suporte",
    processo: "2026/1/1",
    gestor: "Bruno",
    fiscal: "Ana",
    setor: "DGC",
    modalidade: "Pregão Eletrônico",
    inicio: deslocar(-10),
    fim: deslocar(200),
    valor: 1000,
    pago: 100,
    diaPagamento: 10,
    renovavel: false,
    id: "SUPGES/01/2026",
    ...parcial,
  };
}

function estado(contratos, filtro = {}, ordem = { key: "fim", dir: 1 }) {
  return {
    contratos,
    janela: 120,
    limite: 0.85,
    filtro: { q: "", superintendencia: "", setor: "", sit: "", ...filtro },
    ordem,
  };
}

test("situação segue a janela de renovação", () => {
  assert.equal(situacao(contrato({ fim: deslocar(-1) }), 120), "vencido");
  assert.equal(situacao(contrato({ fim: deslocar(30) }), 120), "a-vencer");
  assert.equal(situacao(contrato({ fim: deslocar(200) }), 120), "vigente");
});

test("busca, filtros e ordenação da tabela", () => {
  const carteira = [
    contrato({ id: "a", numero: "01", fornecedor: "Alfa", valor: 1000, pago: 100, fim: deslocar(200) }),
    contrato({ id: "b", numero: "02", fornecedor: "Beta", superintendencia: "SUPSIS", setor: "Sistemas", valor: 400, pago: 390, fim: deslocar(20) }),
    contrato({ id: "c", numero: "03", fornecedor: "Gama", valor: 50, pago: 0, fim: deslocar(-4) }),
  ];
  assert.deepEqual(lista(estado(carteira, { q: "beta" })).map((c) => c.id), ["b"]);
  assert.deepEqual(lista(estado(carteira, { superintendencia: "SUPSIS" })).map((c) => c.id), ["b"]);
  assert.deepEqual(lista(estado(carteira, { sit: "vencido" })).map((c) => c.id), ["c"]);
  const porSaldo = ordenar(carteira, estado(carteira, {}, { key: "saldo", dir: -1 }));
  assert.deepEqual(porSaldo.map((c) => c.id), ["a", "c", "b"]);
  assert.equal(saldo(carteira[1]), 10);
});

test("alertas de vencimento, execução, fiscal e pagamento", () => {
  const carteira = [
    contrato({ id: "ok" }),
    contrato({ id: "vence", fim: deslocar(15), renovavel: true, fiscal: "", diaPagamento: null, pago: 900, valor: 1000 }),
    contrato({ id: "fim", fim: deslocar(-2), fiscal: "Ana", diaPagamento: 5 }),
  ];
  const itens = alertas(estado(carteira));
  const chaves = itens.map((item) => item.id + ":" + item.k);
  assert.ok(chaves.includes("vence:120 dias"));
  assert.ok(chaves.includes("vence:Saldo"));
  assert.ok(chaves.includes("vence:Sem fiscal"));
  assert.ok(chaves.includes("vence:Sem pagamento"));
  assert.ok(chaves.includes("fim:Vencido"));
  assert.equal(itens.some((item) => item.id === "ok"), false);
  assert.equal(proximoPagamento(carteira[2], 120), null);
  const futuro = proximoPagamento(carteira[0], 120);
  assert.ok(futuro instanceof Date);
  assert.ok(futuro <= new Date(carteira[0].fim + "T00:00:00"));
});
