/** Modelo de acesso à API. As telas não montam fetch solto. */

export async function obterPainel() {
  const resposta = await fetch("/api/contratos");
  if (resposta.status === 401) {
    location.href = "/login";
    return null;
  }
  if (!resposta.ok) throw new Error("HTTP " + resposta.status);
  return resposta.json();
}

export async function entrar(usuario, senha) {
  const resposta = await fetch("/api/entrar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, senha }),
  });
  const data = await resposta.json().catch(() => ({}));
  return { ok: resposta.ok, data };
}

export async function sair() {
  await fetch("/api/sair", { method: "POST" });
  location.href = "/login";
}
