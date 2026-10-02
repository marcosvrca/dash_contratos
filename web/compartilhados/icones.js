/** Ícones do menu e da barra superior. A view só pede o nome. */

export const ICONES = {
  home: '<path d="M4 10.5 12 4l8 6.5"/><path d="M6 10v9h4v-5h4v5h4v-9"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M8 13h8M8 17h5"/>',
  receipt: '<path d="M6 3h12v18l-2-1.5L14 21l-2-1.5L10 21l-2-1.5L6 21z"/><path d="M9 8h6M9 12h6"/>',
  clipboard: '<path d="M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1z"/><path d="M8 6H6v14h12V6h-2"/><path d="M9 12h6M9 16h4"/>',
  bank: '<path d="M4 10h16M6 10v7M10 10v7M14 10v7M18 10v7M3 19h18M12 4 3 10h18z"/>',
  search: '<circle cx="11" cy="11" r="6"/><path d="m20 20-3.5-3.5"/>',
  bell: '<path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15z"/><path d="M10 19a2 2 0 0 0 4 0"/>',
  calendar: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>',
  clock: '<circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/>',
  alert: '<circle cx="12" cy="12" r="8"/><path d="M12 8v5M12 16h.01"/>',
  wallet: '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M16 14h2"/>',
  up: '<path d="M6 14l6-6 6 6"/>',
  down: '<path d="M6 10l6 6 6-6"/>',
};

export function svg(nome) {
  return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONES[nome]}</svg>`;
}

export function pintarIcones(raiz = document) {
  raiz.querySelectorAll("[data-ico]").forEach((el) => {
    el.innerHTML = svg(el.dataset.ico);
  });
}
