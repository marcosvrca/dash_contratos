/** View do dashboard: desenha o resumo que o viewmodel entrega. */

import { svg } from "../../compartilhados/icones.js";
import { brl, eixoValor, esc, fmt, parseISO, pct } from "../../compartilhados/formatacao.js";
import { corDe, faixa, niceMax, PALETA, rotulo } from "./dashboard.model.js";

function anel(slices, total, centro, sub) {
  const r = 58;
  const c = 2 * Math.PI * r;
  let acc = 0;
  const arcos = slices
    .filter((s) => s.n > 0)
    .map((s) => {
      const len = total ? (s.n / total) * c : 0;
      const el = `<circle cx="80" cy="80" r="${r}" fill="none" stroke="${s.cor}" stroke-width="16" stroke-dasharray="${len.toFixed(3)} ${(c - len).toFixed(3)}" stroke-dashoffset="${(-acc).toFixed(3)}"/>`;
      acc += len;
      return el;
    })
    .join("");
  const vazio = total ? "" : `<circle cx="80" cy="80" r="${r}" fill="none" stroke="#e6ebf2" stroke-width="16"/>`;
  return `<svg class="donut" viewBox="0 0 160 160" role="img" aria-label="${esc(sub)}">
    <g transform="rotate(-90 80 80)">${vazio}${arcos}</g>
    <text x="80" y="74" text-anchor="middle" font-size="26" font-weight="700" fill="#142033">${esc(centro)}</text>
    <text x="80" y="94" text-anchor="middle" font-size="12" font-weight="600" fill="#6c7a8d">${esc(sub)}</text>
  </svg>`;
}

function legenda(slices, total) {
  return `<ul class="legend">${slices
    .map(
      (s) =>
        `<li><i class="dot" style="background:${s.cor}"></i><span class="nome">${esc(s.nome)}</span><span class="n">${s.n}</span><span class="p">${pct(s.n, total)}</span></li>`
    )
    .join("")}</ul>`;
}

function kpi(ico, tom, label, valor, foot, cls, money) {
  return `<article class="card kpi${money ? " money" : ""}">
    <div class="row"><div class="lbl">${label}</div><div class="ico ${tom}">${svg(ico)}</div></div>
    <div class="val">${valor}</div>
    <div class="foot ${cls}">${foot}</div>
  </article>`;
}

export function pintar(r) {
  const alerta = r.vencidos.length + r.d30.length;
  const badge = document.getElementById("badge");
  badge.hidden = alerta === 0;
  badge.textContent = alerta > 9 ? "9+" : String(alerta);

  const footNovos = r.novos ? `${svg("up")}+${r.novos} no mês` : "nenhum início no mês";
  const footValor =
    r.valorAntes && r.variacao
      ? `${svg(r.variacao > 0 ? "up" : "down")}${r.variacao > 0 ? "+" : ""}${(r.variacao * 100).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}% vs. mês anterior`
      : "sem variação no mês";

  document.getElementById("kpis").innerHTML = [
    kpi("file", "g", "Total de contratos", String(r.total), footNovos, r.novos ? "up" : "flat"),
    kpi("clock", "o", "Vencem em 30 dias", String(r.d30.length), pct(r.d30.length, r.total) + " do total", "warn"),
    kpi("calendar", "y", "Vencem em 90 dias", String(r.d90.length), pct(r.d90.length, r.total) + " do total", "warn"),
    kpi("alert", "r", "Vencidos", String(r.vencidos.length), pct(r.vencidos.length, r.total) + " do total", r.vencidos.length ? "bad" : "flat"),
    kpi(
      "wallet",
      "t",
      "Valor total dos contratos",
      brl(r.valor),
      footValor,
      r.variacao > 0 ? "up" : r.variacao < 0 ? "bad" : "flat",
      true
    ),
  ].join("");

  const status = [
    { nome: "Vigente", n: r.vigentes.length, cor: "#22c55e" },
    { nome: "Até 30 dias", n: r.d30.length, cor: "#f59e0b" },
    { nome: "31 a 90 dias", n: r.entre.length, cor: "#facc15" },
    { nome: "Vencidos", n: r.vencidos.length, cor: "#ef4444" },
  ];
  document.getElementById("status").innerHTML = `<div class="head"><h2>Status dos contratos</h2></div><div class="split">${anel(status, r.total, String(r.total), r.total === 1 ? "contrato" : "contratos")}${legenda(status, r.total)}</div>`;

  const maxN = Math.max(1, ...r.setores.map((s) => s.n));
  document.getElementById("setores").innerHTML = `<div class="head"><h2>Contratos por setor</h2></div><div class="hlist">${
    r.setores.length
      ? r.setores
          .map(
            (s, i) =>
              `<div class="hrow"><div class="hmeta"><span class="hn">${esc(s.nome)}</span><span class="hc">${s.n}</span><span class="hp">${pct(s.n, r.total)}</span></div><div class="htrack"><div class="hfill" style="width:${Math.max(6, s.n / maxN * 100)}%;background:${corDe(s.nome, i)}"></div></div></div>`
          )
          .join("")
      : `<p class="empty">Nenhum contrato neste recorte.</p>`
  }</div>`;

  document.getElementById("vencimentos").innerHTML = `<div class="head"><h2>Vencimentos próximos</h2><a class="link" href="/contratos">Ver todos</a></div><div class="vencs">${
    r.proximos.length
      ? r.proximos
          .map((c) => {
            const f = faixa(c);
            return `<a class="venc" href="/contratos?abrir=${encodeURIComponent(c.id)}"><span class="who">${esc(c.fornecedor)}</span><span class="pill ${f}">${esc(rotulo(c))}</span><span class="meta">${fmt(parseISO(c.fim))} · ${esc(c.setor || "—")}</span></a>`;
          })
          .join("")
      : `<p class="empty">Nenhum vencimento à frente.</p>`
  }</div>`;

  const maxV = niceMax(Math.max(0, ...r.valores.map((s) => s.valor)));
  const ticks = [1, 0.75, 0.5, 0.25, 0].map((p) => eixoValor(maxV * p));
  const altura = 140;
  document.getElementById("valores").innerHTML = `<div class="head"><h2>Valor por setor</h2></div>${
    r.valores.length
      ? `<div class="vchart"><div class="yaxis">${ticks.map((t) => `<span>${esc(t)}</span>`).join("")}</div><div class="vplot"><div class="vlines">${ticks.map(() => "<i></i>").join("")}</div>${r.valores
          .map((s, i) => {
            const h = Math.max(6, Math.round((s.valor / maxV) * altura));
            return `<div class="vcol"><div class="vplotarea"><span class="vcap">${esc(eixoValor(s.valor))}</span><div class="vbar" style="height:${h}px;background:${corDe(s.nome, i)}"></div></div><span class="vlab">${esc(s.nome)}</span></div>`;
          })
          .join("")}</div></div>`
      : `<p class="empty">Nenhum contrato neste recorte.</p>`
  }`;

  const modSlices = r.modalidades.map((m, i) => ({ nome: m.nome, n: m.n, cor: PALETA[i % PALETA.length] }));
  document.getElementById("modalidades").innerHTML = `<div class="head"><h2>Contratos por modalidade</h2></div><div class="split">${anel(modSlices, r.total, String(r.total), r.total === 1 ? "contrato" : "contratos")}${legenda(modSlices, r.total)}</div>`;

  const pPago = r.valor ? Math.round((r.pago / r.valor) * 1000) / 10 : 0;
  const pSaldo = r.valor ? Math.round((r.saldo / r.valor) * 1000) / 10 : 0;
  document.getElementById("financeiro").innerHTML = `<div class="head"><h2>Resumo financeiro</h2></div><div class="fins">
    <div class="fin"><div class="ico t">${svg("wallet")}</div><div><div class="fin-top"><span class="lbl">Valor total contratado</span><b>${brl(r.valor)}</b></div></div></div>
    <div class="fin"><div class="ico b">${svg("file")}</div><div><div class="fin-top"><span class="lbl">Valor pago</span><b>${brl(r.pago)}</b></div><div class="fin-line"><div class="htrack"><div class="hfill" style="width:${Math.min(100, pPago)}%;background:#3b82f6"></div></div><span>${pPago.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%</span></div></div></div>
    <div class="fin"><div class="ico t">${svg("wallet")}</div><div><div class="fin-top"><span class="lbl">Saldo a pagar</span><b>${brl(r.saldo)}</b></div><div class="fin-line"><div class="htrack"><div class="hfill" style="width:${Math.min(100, Math.max(0, pSaldo))}%;background:#7dd3c7"></div></div><span>${pSaldo.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%</span></div></div></div>
  </div>`;

  document.getElementById("recentes").innerHTML = `<div class="head"><h2>Contratos recentes</h2><a class="link" href="/contratos">Ver todos</a></div>
    <div class="tablewrap"><table>
      <thead><tr><th>Nº contrato</th><th>Fornecedor</th><th>Setor</th><th class="r">Valor</th><th>Vigência</th><th>Status</th></tr></thead>
      <tbody>${
        r.recentes.length
          ? r.recentes
              .map(
                (c) => `<tr class="data" data-id="${esc(c.id)}">
        <td>${esc(c.numero)}</td>
        <td>${esc(c.fornecedor)}</td>
        <td><span class="org"><i class="dot" style="background:${corDe(c.setor || "", 0)}"></i>${esc(c.setor || "—")}</span></td>
        <td class="money">${brl(Number(c.valor) || 0)}</td>
        <td>${parseISO(c.fim) ? fmt(parseISO(c.fim)) : "—"}</td>
        <td><span class="pill ${faixa(c)}">${esc(rotulo(c))}</span></td>
      </tr>`
              )
              .join("")
          : `<tr><td class="empty" colspan="6">Nenhum contrato neste recorte.</td></tr>`
      }</tbody>
    </table></div>`;
}

export function mostrarAviso(data, quantidade) {
  const aviso = document.getElementById("aviso");
  const partes = [];
  if (data.ilustrativo) partes.push("<b>Dados ilustrativos.</b> Aponte raizArquivos para a base oficial.");
  if (data.erros && data.erros.length) {
    const textoErros = data.erros.map((e) => (e.faltando || []).join(" ")).join(" ");
    if (/indisponível|não é uma pasta|nenhuma pasta/.test(textoErros) && !quantidade) {
      partes.push("<b>Base de contratos indisponível.</b> " + esc(textoErros));
      aviso.hidden = false;
      aviso.innerHTML = partes.join(" ");
      return;
    }
    const lista = data.erros
      .slice(0, 3)
      .map((e) => {
        const onde = [e.superintendencia, e.numero].filter(Boolean).join(" · ");
        const falta = (e.faltando || []).join(", ");
        return esc(onde ? onde + ": " + falta : falta);
      })
      .join(" · ");
    const extra = data.erros.length > 3 ? " +" + (data.erros.length - 3) : "";
    partes.push("<b>" + data.erros.length + " registro(s) fora do padrão</b> ficaram de fora. " + lista + extra);
  }
  aviso.hidden = partes.length === 0;
  aviso.innerHTML = partes.join(" ");
}

export function mostrarFalha() {
  const aviso = document.getElementById("aviso");
  aviso.hidden = false;
  aviso.innerHTML = "<b>Sistema parado.</b> Execute iniciar.bat na pasta do projeto e abra o endereço mostrado no terminal.";
  document.getElementById("resumo").textContent = "Sem conexão com a base.";
}

export function preencherCabecalho(data) {
  const nome = (data.usuario && data.usuario.nome) || "";
  const cargo = (data.usuario && data.usuario.cargo) || "";
  document.getElementById("orgao").textContent = data.orgaoNome || data.orgao || "ATI";
  document.getElementById("ola").textContent = nome ? "Olá, " + nome : "Olá";
  document.getElementById("unome").textContent = nome || data.orgao || "ATI";
  document.getElementById("ucargo").textContent = cargo || "Gestão de contratos";
  document.title = "Dashboard · " + (data.orgao || "ATI");
}
