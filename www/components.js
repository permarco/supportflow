// SupportFlow · Bausteine fürs Frontend — aus dem Vorprojekt übernommen, in der Demo repariert.
// Verwenden, nicht neu bauen (siehe KONTEXT.md, Abschnitte Stack und Komponenten).
// Farben nur über die Design-Variablen aus variablen.css (A4).

/** Status als Chip, z. B. StatusChip('eskaliert'). */
export function StatusChip(status) {
  const chip = document.createElement('span')
  chip.className = `chip chip-${status}`
  chip.textContent = status
  return chip
}

/** Eine Ticket-Zeile für Listen: Nummer, Titel, Priorität. Ein Link zum Ticket (Tab + Enter). */
export function TicketZeile(t) {
  const zeile = document.createElement('a')
  zeile.className = 'zeile'
  zeile.href = `/posteingang.html?id=${encodeURIComponent(t.id)}`
  const id = document.createElement('span')
  id.className = 'id'
  id.textContent = `#${t.id}`
  const titel = document.createElement('span')
  titel.className = 'titel'
  titel.textContent = t.titel          // Kundentext: anzeigen, nie ausführen
  const prio = document.createElement('span')
  prio.className = `prio prio-${t.prio}`
  prio.textContent = t.prio
  zeile.append(id, titel, prio)
  return zeile
}

/** Grundstil für Chips und Zeilen — einmal in die Seite einbinden. */
export const STIL = `
  .chip { display:inline-block; padding:.1rem .5rem; border-radius:999px; font-size:.85rem; border:1px solid var(--rahmen); }
  .chip-offen { color:var(--offen) } .chip-eskaliert { color:var(--eskaliert) } .chip-erledigt { color:var(--erledigt) }
  .zeile { display:flex; gap:.8rem; padding:.5rem .6rem; border-bottom:1px solid var(--linie); cursor:pointer; color:var(--fg); text-decoration:none; }
  .zeile:hover { background:var(--bg-2) }
  .zeile .id { color:var(--fg-schwach); min-width:4ch } .zeile .titel { flex:1 } .zeile .prio { color:var(--fg-schwach) }
`
