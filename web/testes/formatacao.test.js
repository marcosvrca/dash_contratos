import assert from "node:assert/strict";
import test from "node:test";

import { brlFixo, esc, iniciais, parseISO, pct } from "../compartilhados/formatacao.js";

test("protege texto que vai para o HTML", () => {
  assert.equal(esc(`<b class="a">&'</b>`), "&lt;b class=&quot;a&quot;&gt;&amp;&#39;&lt;/b&gt;");
  assert.equal(esc(null), "");
});

test("formata moeda, percentual e data", () => {
  assert.equal(brlFixo(1250.5), "R$ 1.250,50");
  assert.equal(pct(1, 4), "25,0%");
  assert.equal(pct(1, 0), "0,0%");
  assert.equal(parseISO("2026-04-22")?.getMonth(), 3);
  assert.equal(parseISO("22/04/2026"), null);
  assert.equal(parseISO(""), null);
});

test("monta as iniciais do usuário", () => {
  assert.equal(iniciais("Marcos Vinícius"), "MV");
  assert.equal(iniciais("Ana"), "AN");
  assert.equal(iniciais("  "), "ATI");
});
