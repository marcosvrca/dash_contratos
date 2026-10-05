/** View da carteira: indicadores, gráficos, tabela e ficha. */

import { svg } from "../../compartilhados/icones.js";
import { brlFixo, curtoMil, esc, fmt, hoje, dayMs } from "../../compartilhados/formatacao.js";
import {
  alertas,
  cor,
  grupos,
  lista,
  ordenar,
  parseISO,
  proximoPagamento,
  resumir,
  rotuloSit,
  saldo,
  situacao,
} from "./contratos.model.js";

const NS = "http://www.w3.org/2000/svg";
const COLS = [
  ["numero", "Contrato", "l"],
  ["superintendencia", "Superintendência", "l"],
  ["fornecedor", "Fornecedor", "l"],
  ["setor", "Setor", "l"],
  ["inicio", "Início", ""],
  ["fim", "Fim", ""],
  ["pagamento", "Pagamento", ""],
  ["valor", "Valor", ""],
  ["pago", "Pago", ""],
  ["saldo", "Saldo", ""],
  ["situacao", "Situação", "l"],
];

function el(t, a, p) {
  const e = document.createElementNS(NS, t);
  for (const k in a) e.setAttribute(k, a[k]);
  if (p) p.appendChild(e);
  return e;
}

function kpi(ico, tom, label, valor, foot, cls, money) {
  return `<article class="card kpi${money ? " money" : ""}"><div class="row"><div class="lbl">${label}</div><div class="ico ${tom}">${svg(ico)}</div></div><div class="val">${valor}</div><div class="foot ${cls}">${foot}</div></article>`;
}

let supersKey = "";
function preencherSuperintendencias(ctx) {
  const nomes = [...new Set(ctx.contratos.map((c) => c.superintendencia))].sort((a, b) => a.localeCompare(b, "pt-BR"));
  const key = nomes.join("|");
  if (key === supersKey) return;
  supersKey = key;
  const sel = document.getElementById("fsup");
  const atual = ctx.filtro.superintendencia;
  sel.innerHTML = `<option value="">Todas as superintendências</option>` + nomes.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join("");
  if (nomes.includes(atual)) sel.value = atual;
  else {
    ctx.filtro.superintendencia = "";
    sel.value = "";
  }
}

let setoresKey = "";
function preencherSetores(ctx) {
  const setores = [...new Set(ctx.contratos.map((c) => c.setor))].sort((a, b) => a.localeCompare(b, "pt-BR"));
  const key = setores.join("|");
  if (key === setoresKey) return;
  setoresKey = key;
  const sel = document.getElementById("fset");
  const atual = ctx.filtro.setor;
  sel.innerHTML = `<option value="">Todos os setores</option>` + setores.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join("");
  if (setores.includes(atual)) sel.value = atual;
  else {
    ctx.filtro.setor = "";
    sel.value = "";
  }
}

function renderAlertas(ctx) {
  const items = alertas(ctx);
  const badge = document.getElementById("badge");
  badge.hidden = items.length === 0;
  badge.textContent = items.length > 9 ? "9+" : String(items.length);
  document.getElementById("alerts").innerHTML = items.length
    ? items
        .map(
          (a) =>
            `<button class="alert ${a.cls}" type="button" data-id="${esc(a.id)}"><span><span class="k">${esc(a.k)}</span><div>${esc(a.t)}</div></span><span class="go">Abrir</span></button>`
        )
        .join("")
    : `<p class="empty">Nenhum alerta na carteira.</p>`;
}

function renderKpis(ctx) {
  const rows = lista(ctx);
  const r = resumir(rows, ctx);
  const vencTxt = r.vencidos === 1 ? "1 vencido na visão" : r.vencidos + " vencidos na visão";
  document.getElementById("kpis").innerHTML = [
    kpi("wallet", "t", "Valor global", brlFixo(r.valor), r.escopo, "flat", true),
    kpi("file", "b", "Pago", brlFixo(r.pago), (r.valor ? Math.round((r.pago / r.valor) * 100) : 0) + "% executado", "up", true),
    kpi("wallet", "t", "Saldo", brlFixo(r.valor - r.pago), r.quantidade + (r.quantidade === 1 ? " contrato na visão" : " contratos na visão"), "flat", true),
    kpi("file", "g", "Ativos", String(r.ativos), vencTxt, r.vencidos ? "bad" : "up"),
    kpi(
      "clock",
      "o",
      "Janela de " + ctx.janela + " dias",
      String(r.janela.length),
      brlFixo(r.janela.reduce((s, c) => s + c.valor, 0)) + " em valor global",
      r.janela.length ? "warn" : "flat"
    ),
  ].join("");
}

function renderSetor(ctx, acoes) {
  const rows = lista(ctx);
  const grafico = document.getElementById("cset");
  grafico.replaceChildren();
  const groups = grupos(rows);
  const H = Math.max(180, groups.length * 56 + 28);
  const W = 640;
  const L = 168;
  const R = 16;
  const T = 8;
  const B = 22;
  grafico.setAttribute("viewBox", `0 0 ${W} ${H}`);
  grafico.setAttribute("width", W);
  grafico.setAttribute("height", H);
  if (!groups.length) {
    el("text", { x: 16, y: 28 }, grafico).textContent = "Nenhum contrato neste filtro.";
    return;
  }
  const max = Math.max(...groups.map((g) => g.valor)) * 1.05;
  const x = (v) => L + (v / max) * (W - L - R);
  const rh = (H - T - B) / groups.length;
  const bh = Math.min(18, rh * 0.42);
  groups.forEach((g, i) => {
    const cy = T + rh * i + rh / 2;
    el("text", { x: L - 10, y: cy - 2, "text-anchor": "end", fill: "var(--ink)", style: "font-weight:600" }, grafico).textContent = g.setor;
    el("text", { x: L - 10, y: cy + 12, "text-anchor": "end" }, grafico).textContent = g.n + (g.n > 1 ? " contratos" : " contrato");
    el("rect", { x: L, y: cy - bh / 2, width: Math.max(2, x(g.valor) - L), height: bh, rx: 4, fill: "var(--surface-2)" }, grafico);
    if (g.pago > 0) el("rect", { x: L, y: cy - bh / 2, width: Math.max(2, x(g.pago) - L), height: bh, rx: 4, fill: `var(${cor(g.setor)})` }, grafico);
    el("text", { x: L, y: cy + bh / 2 + 14, class: "tick" }, grafico).textContent = curtoMil(g.pago) + " pago · " + curtoMil(g.valor) + " global";
    const hit = el("rect", { x: 0, y: T + rh * i, width: W, height: rh, fill: "transparent", style: "cursor:pointer" }, grafico);
    hit.addEventListener("click", () => {
      ctx.filtro.superintendencia = ctx.filtro.superintendencia === g.setor ? "" : g.setor;
      document.getElementById("fsup").value = ctx.filtro.superintendencia;
      acoes.atualizar();
    });
  });
}

function renderGantt(ctx) {
  const rows = ordenar(lista(ctx), ctx).sort((a, b) => parseISO(a.inicio) - parseISO(b.inicio));
  const grafico = document.getElementById("cgan");
  grafico.replaceChildren();
  const n = rows.length;
  const H = Math.max(180, n * 28 + 36);
  const W = 560;
  const L = 108;
  const R = 12;
  const T = 16;
  const B = 20;
  grafico.setAttribute("viewBox", `0 0 ${W} ${H}`);
  grafico.setAttribute("width", W);
  grafico.setAttribute("height", H);
  if (!n) {
    el("text", { x: 12, y: 28 }, grafico).textContent = "Nenhum contrato neste filtro.";
    return;
  }
  const min = Math.min(...rows.map((c) => parseISO(c.inicio).getTime()));
  const max = Math.max(...rows.map((c) => parseISO(c.fim).getTime()), hoje.getTime() + dayMs);
  const x = (t) => L + ((t - min) / (max - min)) * (W - L - R);
  const y0 = T;
  const y1 = H - B;
  el("line", { x1: x(hoje), x2: x(hoje), y1: y0, y2: y1, stroke: "var(--ink-3)", "stroke-dasharray": "3 3" }, grafico);
  el("text", { x: x(hoje) + 4, y: 12 }, grafico).textContent = "hoje";
  const janelaFim = hoje.getTime() + ctx.janela * dayMs;
  el(
    "rect",
    {
      x: x(hoje),
      y: y0,
      width: Math.max(0, x(Math.min(janelaFim, max)) - x(hoje)),
      height: y1 - y0,
      fill: "var(--warn-ink)",
      "fill-opacity": "0.08",
    },
    grafico
  );
  const rh = (y1 - y0) / n;
  rows.forEach((c, i) => {
    const cy = y0 + rh * i + rh / 2;
    const s = situacao(c, ctx.janela);
    const tinta = s === "vencido" ? "var(--bad-ink)" : s === "a-vencer" ? "var(--warn-ink)" : "var(--ok-ink)";
    el("text", { x: L - 8, y: cy + 4, "text-anchor": "end", style: "fill:var(--ink-2)" }, grafico).textContent = c.numero;
    const x1 = x(parseISO(c.inicio));
    const x2 = x(parseISO(c.fim));
    el("rect", { x: x1, y: cy - 5, width: Math.max(3, x2 - x1), height: 10, rx: 4, fill: tinta }, grafico);
    const hit = el("rect", { x: 0, y: y0 + rh * i, width: W, height: rh, fill: "transparent", style: "cursor:pointer" }, grafico);
    hit.addEventListener("click", () => abrir(ctx, c.id));
  });
}

export function renderTabela(ctx) {
  const rows = ordenar(lista(ctx), ctx);
  document.getElementById("count").textContent = rows.length + (rows.length === 1 ? " contrato" : " contratos");
  const head = COLS.map(([k, label, cls]) => {
    const mark = ctx.ordem.key === k ? (ctx.ordem.dir > 0 ? " ↑" : " ↓") : "";
    return `<th class="${cls}" data-k="${k}">${label}${mark}</th>`;
  }).join("");
  const body = rows.length
    ? rows
        .map((c) => {
          const pag = proximoPagamento(c, ctx.janela);
          const s = situacao(c, ctx.janela);
          return `<tr class="data" data-id="${esc(c.id)}">
      <td class="l">${esc(c.numero)}</td>
      <td class="l">${esc(c.superintendencia)}</td>
      <td class="l">${esc(c.fornecedor)}</td>
      <td class="l"><span class="org"><i class="dot" style="background:var(${cor(c.setor)})"></i>${esc(c.setor)}</span></td>
      <td>${fmt(parseISO(c.inicio))}</td>
      <td>${fmt(parseISO(c.fim))}</td>
      <td>${pag ? fmt(pag) : "—"}</td>
      <td>${brlFixo(c.valor)}</td>
      <td>${brlFixo(c.pago)}</td>
      <td>${brlFixo(saldo(c))}</td>
      <td class="l"><span class="pill ${s}">${esc(rotuloSit(c, ctx.janela))}</span></td>
    </tr>`;
        })
        .join("")
    : `<tr><td class="l empty" colspan="11">Nenhum contrato encontrado.</td></tr>`;
  document.getElementById("tbl").innerHTML = `<thead><tr>${head}</tr></thead><tbody>${body}</tbody>`;
}

function linha(k, v) {
  return `<span>${esc(k)}</span><b>${esc(v)}</b>`;
}

export function abrir(ctx, id) {
  const c = ctx.contratos.find((x) => x.id === id);
  if (!c) return;
  const pag = proximoPagamento(c, ctx.janela);
  document.getElementById("dnum").textContent = c.numero + " · " + c.modalidade;
  document.getElementById("dforn").textContent = c.fornecedor;
  document.getElementById("dobj").textContent = c.objeto;
  document.getElementById("dbody").innerHTML = `
    <div class="block"><h3>Dados identificadores</h3><div class="kv">
      ${linha("Superintendência", c.superintendencia)}
      ${linha("Pasta", c.pasta || "—")}
      ${linha("Processo", c.processo)}
      ${linha("Modalidade", c.modalidade)}
      ${linha("Setor", c.setor)}
    </div></div>
    <div class="block"><h3>Vigência e prazos</h3><div class="kv">
      ${linha("Assinatura", c.assinatura ? fmt(parseISO(c.assinatura)) : "—")}
      ${linha("Início", fmt(parseISO(c.inicio)))}
      ${linha("Fim", fmt(parseISO(c.fim)))}
      ${linha("Situação", rotuloSit(c, ctx.janela))}
      ${linha("Regra", "Alerta de renovação aos " + ctx.janela + " dias do término")}
      ${linha("Próx. pagamento", pag ? fmt(pag) + (c.diaPagamento ? " · dia " + c.diaPagamento : "") : c.diaPagamento ? "Sem parcela futura" : "Não informado")}
    </div></div>
    <div class="block"><h3>Classificação e vínculos</h3><div class="kv">
      ${linha("Renovável", c.renovavel ? "Sim" : "Não")}
      ${linha("Gestor", c.gestor || "—")}
      ${linha("Fiscal", c.fiscal || "Não atribuído")}
    </div></div>
    <div class="block"><h3>Dotação orçamentária</h3><div class="kv">
      ${linha("Valor global", brlFixo(c.valor))}
      ${linha("Pago", brlFixo(c.pago))}
      ${linha("Saldo", brlFixo(saldo(c)))}
      ${linha("Fonte", c.fonte)}
      ${linha("Programa", c.programa)}
      ${linha("ND", c.nd)}
    </div></div>`;
  document.getElementById("dlg").showModal();
}

export function pintar(ctx, acoes) {
  preencherSuperintendencias(ctx);
  preencherSetores(ctx);
  renderAlertas(ctx);
  renderKpis(ctx);
  renderSetor(ctx, acoes);
  renderGantt(ctx);
  renderTabela(ctx);
}

export function mostrarAviso(data) {
  const aviso = document.getElementById("aviso");
  const partes = [];
  if (data.ilustrativo) {
    partes.push("<b>Dados ilustrativos.</b> Para a base real, aponte raizArquivos em config.json para o servidor de arquivos e marque dadosIlustrativos como false.");
  }
  if (data.erros && data.erros.length) {
    const listaErros = data.erros
      .map((e) => {
        const onde = [e.superintendencia, e.numero || (e.linha ? "linha " + e.linha : "")].filter(Boolean).join(" · ");
        const falta = (e.faltando || []).join(", ");
        return esc(onde ? onde + ": " + falta : falta);
      })
      .join("; ");
    partes.push("<b>" + data.erros.length + " registro(s) fora do padrão</b> ficaram de fora. " + listaErros);
  }
  aviso.hidden = partes.length === 0;
  aviso.innerHTML = partes.join(" ");
}

export function mostrarFalha() {
  const aviso = document.getElementById("aviso");
  aviso.hidden = false;
  aviso.innerHTML = "<b>Sistema parado.</b> Execute scripts\\iniciar.bat e abra o endereço mostrado no terminal.";
  document.getElementById("fonte").textContent = "Sem conexão com a base";
}

export function preencherCabecalho(data, janela) {
  const nome = (data.usuario && data.usuario.nome) || "";
  const cargo = (data.usuario && data.usuario.cargo) || "";
  document.getElementById("orgao").textContent = data.orgaoNome || data.orgao || "ATI";
  document.getElementById("unome").textContent = nome || data.orgao || "ATI";
  document.getElementById("ucargo").textContent = cargo || "Gestão de contratos";
  document.title = "Contratos · " + (data.orgao || "ATI");
  document.getElementById("fonte").textContent = (data.ilustrativo ? "Base ilustrativa" : "Carteira oficial") + " · janela de renovação de " + janela + " dias";
  const janelaOpt = document.querySelector('#fsit option[value="a-vencer"]');
  if (janelaOpt) janelaOpt.textContent = "A vencer em " + janela + " dias";
  const legenda = document.getElementById("legenda-vigencia");
  if (legenda) legenda.children[1].lastChild.textContent = janela + " dias";
}
