/** Modelo da carteira: situação, filtros, ordem e alertas. Sem DOM. */

import { dayMs, hoje } from "../../compartilhados/formatacao.js";

export function parseISO(s) {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function diasAte(fim) {
  return Math.ceil((parseISO(fim) - hoje) / dayMs);
}

export function situacao(c, janela) {
  const d = diasAte(c.fim);
  if (d < 0) return "vencido";
  if (d <= janela) return "a-vencer";
  return "vigente";
}

export function rotuloSit(c, janela) {
  const s = situacao(c, janela);
  const d = diasAte(c.fim);
  if (s === "vencido") return "Vencido há " + Math.abs(d) + " dias";
  if (s === "a-vencer") return "Vence em " + d + " dias";
  return "Vigente";
}

export function proximoPagamento(c, janela) {
  if (!c.diaPagamento || situacao(c, janela) === "vencido") return null;
  const fim = parseISO(c.fim);
  let d = new Date(hoje.getFullYear(), hoje.getMonth(), c.diaPagamento);
  if (d < hoje) d = new Date(hoje.getFullYear(), hoje.getMonth() + 1, c.diaPagamento);
  if (d > fim) return null;
  return d;
}

export function saldo(c) {
  return c.valor - c.pago;
}

export function lista(ctx) {
  const q = ctx.filtro.q.trim().toLowerCase();
  return ctx.contratos.filter((c) => {
    if (ctx.filtro.superintendencia && c.superintendencia !== ctx.filtro.superintendencia) return false;
    if (ctx.filtro.setor && c.setor !== ctx.filtro.setor) return false;
    if (ctx.filtro.sit && situacao(c, ctx.janela) !== ctx.filtro.sit) return false;
    if (!q) return true;
    const blob = [c.numero, c.superintendencia, c.fornecedor, c.objeto, c.processo, c.gestor, c.fiscal, c.setor, c.modalidade]
      .join(" ")
      .toLowerCase();
    return blob.includes(q);
  });
}

export function ordenar(rows, ctx) {
  const k = ctx.ordem.key;
  const val = (c) => {
    if (k === "saldo") return saldo(c);
    if (k === "pagamento") return proximoPagamento(c, ctx.janela)?.getTime() ?? 0;
    if (k === "inicio" || k === "fim") return parseISO(c[k]).getTime();
    if (k === "situacao") return diasAte(c.fim);
    return c[k];
  };
  return [...rows].sort((a, b) => {
    const va = val(a);
    const vb = val(b);
    if (va < vb) return -ctx.ordem.dir;
    if (va > vb) return ctx.ordem.dir;
    return a.numero.localeCompare(b.numero);
  });
}

export function alertas(ctx) {
  const items = [];
  ctx.contratos.forEach((c) => {
    const s = situacao(c, ctx.janela);
    if (s === "vencido") {
      items.push({
        cls: "bad",
        k: "Vencido",
        t: c.numero + " · " + c.fornecedor + " encerrou em " + fmtData(c.fim) + ".",
        id: c.id,
      });
    } else if (s === "a-vencer") {
      items.push({
        cls: "warn",
        k: ctx.janela + " dias",
        t: c.numero + " · " + c.fornecedor + " vence em " + diasAte(c.fim) + " dias" + (c.renovavel ? " · renovável" : "") + ".",
        id: c.id,
      });
    }
    if (c.valor > 0 && c.pago / c.valor >= ctx.limite && s !== "vencido") {
      items.push({
        cls: "warn",
        k: "Saldo",
        t: c.numero + " · execução em " + Math.round((c.pago / c.valor) * 100) + "% do valor global.",
        id: c.id,
      });
    }
    if (!c.fiscal) items.push({ cls: "bad", k: "Sem fiscal", t: c.numero + " · " + c.fornecedor + " está sem fiscal atribuído.", id: c.id });
    if (!c.diaPagamento) items.push({ cls: "warn", k: "Sem pagamento", t: c.numero + " · dia de pagamento não informado.", id: c.id });
  });
  return items;
}

function fmtData(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("pt-BR");
}

export function resumir(rows, ctx) {
  const valor = rows.reduce((s, c) => s + c.valor, 0);
  const pago = rows.reduce((s, c) => s + c.pago, 0);
  const ativos = rows.filter((c) => situacao(c, ctx.janela) !== "vencido").length;
  const vencidos = rows.length - ativos;
  const janela = rows.filter((c) => situacao(c, ctx.janela) === "a-vencer");
  const escopo = ctx.filtro.q || ctx.filtro.superintendencia || ctx.filtro.setor || ctx.filtro.sit ? "Visão filtrada" : "Carteira";
  return { valor, pago, ativos, vencidos, janela, escopo, quantidade: rows.length };
}

export function grupos(rows) {
  const map = new Map();
  rows.forEach((c) => {
    const nome = c.superintendencia || "Sem superintendência";
    const g = map.get(nome) || { setor: nome, valor: 0, pago: 0, n: 0 };
    g.valor += c.valor;
    g.pago += c.pago;
    g.n += 1;
    map.set(nome, g);
  });
  return [...map.values()].sort((a, b) => b.valor - a.valor);
}

const CORES = {
  Infraestrutura: "--s1",
  Sistemas: "--s2",
  Suporte: "--s3",
  "Segurança da Informação": "--s4",
  Administrativo: "--s5",
};
const PALETA = ["--s1", "--s2", "--s3", "--s4", "--s5"];

export function cor(setor) {
  if (CORES[setor]) return CORES[setor];
  let h = 0;
  for (const ch of setor) h = (h + ch.charCodeAt(0)) % PALETA.length;
  return PALETA[h];
}
