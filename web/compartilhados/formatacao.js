/** Formatação compartilhada pelas telas. */

export const dayMs = 86400000;

export const hoje = (() => {
  const t = new Date();
  t.setHours(0, 0, 0, 0);
  return t;
})();

export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

export function brl(n) {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function brlFixo(n) {
  return "R$ " + n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function pct(n, d) {
  return (d ? (n / d) * 100 : 0).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
}

export function parseISO(s) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(s || ""))) return null;
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function fmt(d) {
  return d.toLocaleDateString("pt-BR");
}

export function iniciais(nome) {
  const p = String(nome || "").trim().split(/\s+/).filter(Boolean);
  if (p.length === 0) return "ATI";
  if (p.length === 1) return p[0].slice(0, 2).toUpperCase();
  return (p[0][0] + p[p.length - 1][0]).toUpperCase();
}

export function textoHoje(data = hoje) {
  const meses = ["jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."];
  return String(data.getDate()).padStart(2, "0") + " de " + meses[data.getMonth()] + " de " + data.getFullYear();
}

export function eixoValor(n) {
  const abs = Math.abs(n);
  if (abs >= 1e6) return (n / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mi";
  if (abs >= 1e3) return Math.round(n / 1e3).toLocaleString("pt-BR") + " mil";
  return Math.round(n).toLocaleString("pt-BR");
}

export function curto(n) {
  const abs = Math.abs(n);
  const sinal = n < 0 ? "-" : "";
  if (abs >= 1e6) return sinal + "R$ " + (abs / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mi";
  if (abs >= 1e3) return sinal + "R$ " + Math.round(abs / 1e3).toLocaleString("pt-BR") + " mil";
  return brl(n);
}

export function curtoMil(n) {
  return n >= 1e6
    ? (n / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mi"
    : Math.round(n / 1e3) + " mil";
}
