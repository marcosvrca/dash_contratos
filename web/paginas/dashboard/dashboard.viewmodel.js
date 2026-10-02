/** ViewModel do dashboard: estado da tela, eventos e orquestração. */

import { obterPainel, sair } from "../../compartilhados/api.js";
import { iniciais, textoHoje } from "../../compartilhados/formatacao.js";
import { pintarIcones } from "../../compartilhados/icones.js";
import { filtrar, resumir } from "./dashboard.model.js";
import { mostrarAviso, mostrarFalha, pintar, preencherCabecalho } from "./dashboard.view.js";

const estado = {
  base: [],
  periodo: "12m",
  busca: "",
};

function atualizar() {
  pintar(resumir(filtrar(estado.base, estado.periodo, estado.busca)));
}

async function carregar() {
  document.getElementById("hoje").textContent = textoHoje();
  try {
    const data = await obterPainel();
    if (!data) return;
    estado.base = data.contratos || [];
    const nome = (data.usuario && data.usuario.nome) || "";
    preencherCabecalho(data);
    document.getElementById("avatar").textContent = iniciais(nome || data.orgao || "ATI");
    mostrarAviso(data, estado.base.length);
    atualizar();
  } catch (erro) {
    mostrarFalha();
    atualizar();
  }
}

pintarIcones();
document.getElementById("q").addEventListener("input", (e) => {
  estado.busca = e.target.value;
  atualizar();
});
document.getElementById("periodo").addEventListener("change", (e) => {
  estado.periodo = e.target.value;
  atualizar();
});
document.getElementById("bell").addEventListener("click", () => {
  document.getElementById("vencimentos").scrollIntoView({ behavior: "smooth", block: "center" });
});
document.getElementById("recentes").addEventListener("click", (e) => {
  const tr = e.target.closest("tr.data");
  if (tr) location.href = "/contratos?abrir=" + encodeURIComponent(tr.dataset.id);
});
document.getElementById("sair").addEventListener("click", () => sair());
carregar();
