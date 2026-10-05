import assert from "node:assert/strict";
import test from "node:test";

import { dayMs, hoje } from "../compartilhados/formatacao.js";
import { agrupar, diasAte, faixa, filtrar, niceMax, resumir, rotulo } from "../paginas/dashboard/dashboard.model.js";

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
    numero: "1",
    fornecedor: "Alfa",
    setor: "Sistemas",
    objeto: "suporte",
    processo: "",
    modalidade: "Pregão Eletrônico",
    superintendencia: "SUPGES",
    gestor: "",
    fiscal: "",
    inicio: deslocar(-30),
    fim: deslocar(200),
    valor: 1000,
    pago: 100,
    id: "SUPGES/1",
    ...parcial,
  };
}

test("classifica vencimento pela data de fim", () => {
  assert.equal(faixa(contrato({ fim: deslocar(-2) })), "bad");
  assert.equal(faixa(contrato({ fim: deslocar(10) })), "d30");
  assert.equal(faixa(contrato({ fim: deslocar(60) })), "d90");
  assert.equal(faixa(contrato({ fim: deslocar(200) })), "ok");
  assert.equal(rotulo(contrato({ fim: deslocar(0) })), "Vence hoje");
  assert.equal(rotulo(contrato({ fim: deslocar(1) })), "Vence em 1 dia");
  assert.equal(diasAte("data-ruim"), null);
});

test("filtra período, busca e resume a carteira", () => {
  const base = [
    contrato({ id: "a", fornecedor: "Alfa Sistemas", valor: 1000, fim: deslocar(10) }),
    contrato({ id: "b", fornecedor: "Beta", setor: "Infraestrutura", valor: 500, fim: deslocar(-3), inicio: deslocar(-400) }),
    contrato({ id: "c", fornecedor: "Gama", valor: 250, inicio: "1990-01-01", fim: "1990-12-31" }),
  ];
  const tudo = filtrar(base, "tudo", "alfa");
  assert.deepEqual(tudo.map((c) => c.id), ["a"]);

  const dozeMeses = filtrar(base, "12m", "");
  assert.ok(dozeMeses.some((c) => c.id === "a"));
  assert.equal(dozeMeses.some((c) => c.id === "c"), false);

  const resumo = resumir(filtrar(base, "tudo", ""));
  assert.equal(resumo.total, 3);
  assert.equal(resumo.valor, 1750);
  assert.equal(resumo.pago, 300);
  assert.equal(resumo.d30.length, 1);
  assert.equal(resumo.vencidos.length, 2);
  assert.equal(resumo.proximos[0].id, "a");
});

test("agrupa setores e limita a escala do gráfico", () => {
  const linhas = ["Sistemas", "Infraestrutura", "Suporte", "Administrativo", "Segurança", "Outra"].map((setor, i) =>
    contrato({ id: String(i), setor, valor: (i + 1) * 100 })
  );
  const grupos = agrupar(linhas, "setor", 3, "n");
  assert.equal(grupos.length, 3);
  assert.equal(grupos[grupos.length - 1].nome, "Outros");
  assert.equal(grupos[grupos.length - 1].n, 4);
  assert.equal(niceMax(0), 1);
  assert.ok(niceMax(1500) >= 1500);
});
