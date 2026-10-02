/** ViewModel do login: valida o destino e envia as credenciais. */

import { entrar } from "../../compartilhados/api.js";

const params = new URLSearchParams(location.search);
const next = params.get("next") || "/";
const destino = next.startsWith("/") && !next.startsWith("//") ? next : "/";
const erro = document.getElementById("erro");
const botao = document.getElementById("entrar");

document.getElementById("form").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  erro.hidden = true;
  botao.disabled = true;
  try {
    const resultado = await entrar(document.getElementById("usuario").value, document.getElementById("senha").value);
    if (!resultado.ok) {
      erro.textContent = resultado.data.erro || "Não foi possível entrar.";
      erro.hidden = false;
      botao.disabled = false;
      return;
    }
    location.href = destino;
  } catch (falha) {
    erro.textContent = "Sem conexão com o sistema.";
    erro.hidden = false;
    botao.disabled = false;
  }
});
