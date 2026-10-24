// SupportFlow · Statusübersicht für die Teamleitung.
// Zähler je Status, darunter die eskalierten Tickets. Daten: GET /api/tickets.

import { StatusChip, TicketZeile, STIL } from './components.js'

const STATUS = ['offen', 'eskaliert', 'erledigt']
const stand = document.getElementById('stand')
const liste = document.getElementById('eskaliert')

document.head.append(Object.assign(document.createElement('style'), { textContent: STIL }))

function kachel(status, wert) {
  const el = document.createElement('div')
  el.className = 'kachel'
  el.dataset.status = status
  const zahl = document.createElement('span')
  zahl.className = 'zahl'
  zahl.textContent = wert
  el.append(StatusChip(status), zahl)
  return el
}

function zeigeStand(tickets) {
  stand.replaceChildren(...STATUS.map(s =>
    kachel(s, tickets ? String(tickets.filter(t => t.status === s).length) : '–')))
}

function zeigeListe(tickets) {
  const eskaliert = tickets.filter(t => t.status === 'eskaliert')
  if (eskaliert.length === 0) {
    const p = document.createElement('p')
    p.className = 'leer'
    p.textContent = 'Keine eskalierten Tickets.'
    liste.replaceChildren(p)
    return
  }
  liste.replaceChildren(...eskaliert.map(TicketZeile))
}

// In der Liste: Pfeil auf/ab wechselt die Zeile, Enter öffnet (Standard des Links).
liste.addEventListener('keydown', ev => {
  if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return
  const zeilen = [...liste.querySelectorAll('a.zeile')]
  const i = zeilen.indexOf(document.activeElement)
  if (i < 0) return
  const ziel = zeilen[i + (ev.key === 'ArrowDown' ? 1 : -1)]
  if (ziel) { ev.preventDefault(); ziel.focus() }
})

function zeigeFehler() {
  const box = document.createElement('div')
  box.className = 'meldung'
  box.setAttribute('role', 'alert')
  box.textContent = 'Ticket-Service nicht erreichbar. Keine Daten geladen.'
  const knopf = document.createElement('button')
  knopf.type = 'button'
  knopf.textContent = 'Erneut laden'
  knopf.addEventListener('click', laden)
  box.append(knopf)
  liste.replaceChildren(box)
}

export async function laden() {
  try {
    const antwort = await fetch('/api/tickets')
    if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`)
    const tickets = await antwort.json()
    zeigeStand(tickets)
    zeigeListe(tickets)
  } catch {
    zeigeStand(null)
    zeigeFehler()
  }
}

laden()
