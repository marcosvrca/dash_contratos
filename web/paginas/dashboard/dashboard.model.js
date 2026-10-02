/** Modelo do dashboard: filtros, prazos e agregações. Sem DOM. */

import { dayMs, hoje, parseISO } from "../../compartilhados/formatacao.js";

const CORES = {
  Sistemas: "#3b82f6",
  Infraestrutura: "#14b8a6",
  Suporte: "#8b5cf6",
  Administrativo: "#f59e0b",
  "Segurança da Informação": "#ef4444",
  Outros: "#94a3b8",
  "Não informado": "#94a3b8",
};

export const PALETA = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#14b8a6", "#ef4444", "#64748b"];

export function diasAte(fim, referencia = hoje) {
  const d = parseISO(fim);
  if (!d) return null;
  return Math.ceil((d - referencia) / dayMs);
}

export function faixa(c) {
  const d = diasAte(c.fim);
  if (d == null) return "ok";
  if (d < 0) return "bad";
  if (d <= 30) return "d30";
  if (d <= 90) return "d90";
  return "ok";
}

export function rotulo(c) {
  const d = diasAte(c.fim);
  if (d == null) return "Vigente";
  if (d < 0) return "Vencido há " + Math.abs(d) + (Math.abs(d) === 1 ? " dia" : " dias");
  if (d === 0) return "Vence hoje";
  if (d <= 90) return "Vence em " + d + (d === 1 ? " dia" : " dias");
  return "Vigente";
}

export function corDe(nome, i) {
  return CORES[nome] || PALETA[i % PALETA.length];
}

export function agrupar(rows, campo, limite, por) {
  const map = new Map();
  rows.forEach((c) => {
    const nome = String(c[campo] || "").trim() || "Não informado";
    const g = map.get(nome) || { nome, n: 0, valor: 0 };
    g.n += 1;
    g.valor += Number(c.valor) || 0;
    map.set(nome, g);
  });
  let all = [...map.values()].sort((a, b) => (por === "valor" ? b.valor - a.valor : b.n - a.n));
  if (all.length > limite) {
    const top = all.slice(0, limite - 1);
    const rest = all.slice(limite - 1);
    top.push({
      nome: "Outros",
      n: rest.reduce((s, g) => s + g.n, 0),
      valor: rest.reduce((s, g) => s + g.valor, 0),
    });
    all = top;
  }
  return all;
}

export function niceMax(n) {
  if (n <= 0) return 1;
  const pot = Math.pow(10, Math.floor(Math.log10(n)));
  const passo = [1, 2, 2.5, 4, 5, 10].map((x) => x * pot).find((x) => x >= n);
  return passo || n;
}

function noPeriodo(c, modo) {
  if (modo === "tudo") return true;
  const iniC = parseISO(c.inicio);
  const fimC = parseISO(c.fim);
  if (!iniC || !fimC) return true;
  let ini;
  let fim;
  if (modo === "ano") {
    ini = new Date(hoje.getFullYear(), 0, 1);
    fim = new Date(hoje.getFullYear(), 11, 31);
  } else {
    fim = hoje;
    ini = new Date(hoje.getTime() - 365 * dayMs);
  }
  return iniC <= fim && fimC >= ini;
}

function busca(c, q) {
  const texto = String(q || "").trim().toLowerCase();
  if (!texto) return true;
  return [c.numero, c.fornecedor, c.setor, c.objeto, c.processo, c.modalidade, c.superintendencia, c.gestor, c.fiscal]
    .join(" ")
    .toLowerCase()
    .includes(texto);
}

export function filtrar(base, periodo, consulta) {
  return base.filter((c) => noPeriodo(c, periodo) && busca(c, consulta));
}

export function resumir(rows) {
  const total = rows.length;
  const d30 = rows.filter((c) => {
    const d = diasAte(c.fim);
    return d != null && d >= 0 && d <= 30;
  });
  const d90 = rows.filter((c) => {
    const d = diasAte(c.fim);
    return d != null && d >= 0 && d <= 90;
  });
  const entre = rows.filter((c) => {
    const d = diasAte(c.fim);
    return d != null && d > 30 && d <= 90;
  });
  const vencidos = rows.filter((c) => {
    const d = diasAte(c.fim);
    return d != null && d < 0;
  });
  const vigentes = rows.filter((c) => {
    const d = diasAte(c.fim);
    return d == null || d > 90;
  });
  const valor = rows.reduce((s, c) => s + (Number(c.valor) || 0), 0);
  const pago = rows.reduce((s, c) => s + (Number(c.pago) || 0), 0);
  const saldo = valor - pago;
  const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
  const novos = rows.filter((c) => {
    const d = parseISO(c.inicio);
    return d && d >= inicioMes && d <= hoje;
  }).length;
  const valorAntes = rows
    .filter((c) => {
      const d = parseISO(c.inicio);
      return d && d < inicioMes;
    })
    .reduce((s, c) => s + (Number(c.valor) || 0), 0);
  const variacao = valorAntes ? (valor - valorAntes) / valorAntes : 0;
  const proximos = rows
    .filter((c) => {
      const d = diasAte(c.fim);
      return d != null && d >= 0;
    })
    .sort((a, b) => diasAte(a.fim) - diasAte(b.fim))
    .slice(0, 5);
  const recentes = [...rows]
    .sort((a, b) => (parseISO(b.inicio)?.getTime() || 0) - (parseISO(a.inicio)?.getTime() || 0))
    .slice(0, 8);
  return {
    rows,
    total,
    d30,
    d90,
    entre,
    vencidos,
    vigentes,
    valor,
    pago,
    saldo,
    novos,
    variacao,
    valorAntes,
    setores: agrupar(rows, "setor", 5, "n"),
    valores: agrupar(rows, "setor", 5, "valor"),
    modalidades: agrupar(rows, "modalidade", 5, "n"),
    proximos,
    recentes,
  };
}
