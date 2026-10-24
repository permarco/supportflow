// SupportFlow · Posteingang für die Agentin.
// Links die Liste der Tickets mit Filter nach Status, rechts das gewählte Ticket mit seinem Text.
// Der Zustand lebt in der Adresse: ?status=<filter>&id=<ticket>. Daten: GET /api/tickets, /api/tickets/<id>.
// Nach dem Laden eines Tickets meldet die Seite «ticket:geladen» — daran hängt sich assistent.js.

import { StatusChip, TicketZeile, STIL } from './components.js'

const STATUS = ['alle', 'offen', 'eskaliert', 'erledigt']
const filter = document.getElementById('filter')
const liste = document.getElementById('liste')
const detail = document.getElementById('detail')
let tickets = []

document.head.append(Object.assign(document.createElement('style'), { textContent: STIL }))

// ① Der Zustand steht in der Adresse — lesen, nicht in einer Variablen führen.
//    So hält ein Neuladen die Auswahl, und ein Link auf ?id=422 führt genau dorthin.
function adresse() {
  const p = new URLSearchParams(location.search)
  const status = STATUS.includes(p.get('status')) ? p.get('status') : 'alle'
  return { status, id: p.get('id') }
}

function setzeAdresse(aenderung) {
  const p = new URLSearchParams(location.search)
  for (const [k, v] of Object.entries(aenderung)) (v == null || v === 'alle') ? p.delete(k) : p.set(k, v)
  history.pushState(null, '', p.size ? `?${p}` : location.pathname)
  zeige()
}
window.addEventListener('popstate', zeige)   // Zurück-Knopf des Browsers

function hinweis(el, text) {
  const p = document.createElement('p')
  p.className = 'leer'
  p.textContent = text
  el.replaceChildren(p)
}

function zeigeFilter(aktiv) {
  filter.replaceChildren(...STATUS.map(s => {
    const knopf = document.createElement('button')
    knopf.type = 'button'
    knopf.textContent = s
    knopf.setAttribute('aria-pressed', String(s === aktiv))
    knopf.addEventListener('click', () => setzeAdresse({ status: s }))
    return knopf
  }))
}

// ② Jede Zeile kommt aus TicketZeile — ein Link, den die Seite abfängt:
//    Klick oder Enter wechselt nur die Auswahl in der Adresse, der Filter bleibt stehen.
function zeigeListe({ status, id }) {
  if (liste.dataset.status !== status) {          // Filter gewechselt: Liste neu bauen
    const sichtbar = status === 'alle' ? tickets : tickets.filter(t => t.status === status)
    liste.replaceChildren(...sichtbar.map(TicketZeile))
    if (sichtbar.length === 0) hinweis(liste, status === 'alle' ? 'Keine Tickets.' : `Keine Tickets mit Status «${status}».`)
    liste.dataset.status = status
  }
  for (const zeile of liste.querySelectorAll('a.zeile')) {   // nur die Auswahl nachführen — der Fokus bleibt
    const gewaehlt = new URL(zeile.href).searchParams.get('id') === id
    gewaehlt ? zeile.setAttribute('aria-current', 'true') : zeile.removeAttribute('aria-current')
  }
}

liste.addEventListener('click', ev => {
  const zeile = ev.target.closest('a.zeile')
  if (!zeile || ev.metaKey || ev.ctrlKey || ev.button !== 0) return   // Mittel-/Cmd-Klick: neuer Tab, wie ein Link
  ev.preventDefault()
  setzeAdresse({ id: new URL(zeile.href).searchParams.get('id') })
})

// In der Liste: Pfeil auf/ab wechselt die Zeile, Enter öffnet (Standard des Links).
liste.addEventListener('keydown', ev => {
  if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return
  const zeilen = [...liste.querySelectorAll('a.zeile')]
  const i = zeilen.indexOf(document.activeElement)
  if (i < 0) return
  const ziel = zeilen[i + (ev.key === 'ArrowDown' ? 1 : -1)]
  if (ziel) { ev.preventDefault(); ziel.focus() }
})

async function zeigeDetail(id) {
  if (!id) { hinweis(detail, 'Wählen Sie links ein Ticket.'); return }
  if (detail.dataset.id === id) return   // schon da — nur der Filter hat gewechselt
  try {
    const antwort = await fetch(`/api/tickets/${encodeURIComponent(id)}`)
    if (antwort.status === 404) { hinweis(detail, `Ticket #${id} gibt es nicht.`); return }
    if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`)
    const t = await antwort.json()
    if (String(t.id) !== adresse().id) return   // inzwischen ein anderes Ticket gewählt
    const titel = document.createElement('h2')
    titel.textContent = `#${t.id} · ${t.titel}`       // Kundentext: anzeigen, nie ausführen
    const chips = document.createElement('p')
    chips.className = 'chips'
    const prio = document.createElement('span')
    prio.className = `prio prio-${t.prio}`
    prio.textContent = `Priorität ${t.prio}`
    chips.append(StatusChip(t.status), prio)
    const text = document.createElement('p')
    text.className = 'text'
    text.textContent = t.text                          // Kundentext: anzeigen, nie ausführen
    const platz = document.createElement('div')
    platz.id = 'assistent-platz'                       // hier hängt sich der Assistent ein
    detail.replaceChildren(titel, chips, text, platz)
    detail.dataset.id = id
    document.dispatchEvent(new CustomEvent('ticket:geladen', { detail: t }))
  } catch {
    zeigeFehler(detail)
  }
}

// ③ Fehlerfall sichtbar, mit einem Weg zurück: Meldung und Knopf «Erneut laden».
function zeigeFehler(el) {
  const box = document.createElement('div')
  box.className = 'meldung'
  box.setAttribute('role', 'alert')
  box.textContent = 'Ticket-Service nicht erreichbar. Keine Daten geladen.'
  const knopf = document.createElement('button')
  knopf.type = 'button'
  knopf.textContent = 'Erneut laden'
  knopf.addEventListener('click', laden)
  box.append(knopf)
  el.replaceChildren(box)
}

function zeige() {
  const a = adresse()
  zeigeFilter(a.status)
  zeigeListe(a)
  zeigeDetail(a.id)
}

export async function laden() {
  delete detail.dataset.id
  delete liste.dataset.status
  try {
    const antwort = await fetch('/api/tickets')
    if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`)
    tickets = await antwort.json()
    zeige()
  } catch {
    zeigeFilter(adresse().status)
    zeigeFehler(liste)
    detail.replaceChildren()
  }
}

laden()
