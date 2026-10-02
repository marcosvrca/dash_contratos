/** ViewModel da carteira: filtros, ordenação e carga da base. */

import { obterPainel, sair } from "../../compartilhados/api.js";
import { iniciais, textoHoje } from "../../compartilhados/formatacao.js";
import { pintarIcones } from "../../compartilhados/icones.js";
import { abrir, mostrarAviso, mostrarFalha, pintar, preencherCabecalho, renderTabela } from "./contratos.view.js";

const estado = {
  contratos: [],
  janela: 120,
  limite: 0.85,
  filtro: { q: "", superintendencia: "", setor: "", sit: "" },
  ordem: { key: "fim", dir: 1 },
};

function atualizar() {
  pintar(estado, { atualizar });
}

async function carregar() {
  try {
    const data = await obterPainel();
    if (!data) return;
    estado.contratos = data.contratos || [];
    estado.janela = data.regras.janelaRenovacaoDias;
    estado.limite = data.regras.limiteExecucao;
    const nome = (data.usuario && data.usuario.nome) || "";
    document.getElementById("avatar").textContent = iniciais(nome || data.orgao || "ATI");
    preencherCabecalho(data, estado.janela);
    const qs = new URLSearchParams(location.search);
    if (qs.get("q")) {
      estado.filtro.q = qs.get("q");
      document.getElementById("q").value = estado.filtro.q;
    }
    mostrarAviso(data);
    atualizar();
    if (qs.get("abrir")) abrir(estado, qs.get("abrir"));
  } catch (erro) {
    mostrarFalha();
  }
}

pintarIcones();
document.getElementById("hoje").textContent = textoHoje();
document.getElementById("q").addEventListener("input", (e) => {
  estado.filtro.q = e.target.value;
  atualizar();
});
document.getElementById("fsup").addEventListener("change", (e) => {
  estado.filtro.superintendencia = e.target.value;
  atualizar();
});
document.getElementById("fset").addEventListener("change", (e) => {
  estado.filtro.setor = e.target.value;
  atualizar();
});
document.getElementById("fsit").addEventListener("change", (e) => {
  estado.filtro.sit = e.target.value;
  atualizar();
});
document.getElementById("tbl").addEventListener("click", (e) => {
  const th = e.target.closest("th");
  if (th) {
    const k = th.dataset.k;
    estado.ordem = estado.ordem.key === k
      ? { key: k, dir: -estado.ordem.dir }
      : { key: k, dir: k === "fornecedor" || k === "setor" || k === "numero" || k === "superintendencia" ? 1 : -1 };
    renderTabela(estado);
    return;
  }
  const tr = e.target.closest("tr.data");
  if (tr) abrir(estado, tr.dataset.id);
});
document.getElementById("alerts").addEventListener("click", (e) => {
  const b = e.target.closest("[data-id]");
  if (b) abrir(estado, b.dataset.id);
});
document.getElementById("bell").addEventListener("click", () => {
  document.getElementById("alertas").scrollIntoView({ behavior: "smooth", block: "center" });
});
document.getElementById("dx").addEventListener("click", () => document.getElementById("dlg").close());
document.getElementById("dlg").addEventListener("click", (e) => {
  if (e.target.id === "dlg") e.currentTarget.close();
});
document.getElementById("sair").addEventListener("click", () => sair());
carregar();
