// SupportFlow · Assistent im Ticket-Detail (A8).
// Knopf «Antwortentwurf erzeugen» → zwei Anfragen an unseren Service (heute der Mock):
//   GET /api/suggest?ticket=<id>  → Einschätzung als JSON, am Stück
//   GET /api/draft?ticket=<id>    → Antwortentwurf als Strom (SSE), Wort für Wort
// Fünf Zustände: wartet · strömt · fertig · abgebrochen · fehler. Stopp schliesst die Verbindung.
// Stufen (KONTEXT.md, Abschnitt «Assistent»): Vorschlag autonom · senden/eskalieren/schliessen mit Bestätigung · alles andere: kein Element.

import { StatusChip } from './components.js'

const ERLAUBT = {                                  // ① nur bekannte Aktionen bekommen ein Element — Form nach Stufe
  antworten:  { text: 'Antwort übernehmen', stufe: 'autonom' },
  eskalieren: { text: 'Eskalieren …',       stufe: 'bestaetigung' },
  schliessen: { text: 'Ticket schliessen …', stufe: 'bestaetigung' },
}
const TIMEOUT_MS = 5000                            // antwortet der Service nicht, Zustand «fehler» — nie ewig «wartet»

let ticket = null
let abbruch = null                                 // AbortController des laufenden Stroms
let ui = null

function el(tag, props = {}, ...kinder) {
  const e = Object.assign(document.createElement(tag), props)
  e.append(...kinder)
  return e
}

// Die Weichen der Seite (?slow=1 · ?fail=1 · ?bad=1) an den Service weiterreichen — nur zum Prüfen.
function apiParams() {
  const p = new URLSearchParams(location.search)
  const q = new URLSearchParams({ ticket: ticket.id })
  for (const k of ['slow', 'fail', 'bad']) if (p.get(k)) q.set(k, p.get(k))
  return q.toString()
}

function baue(platz) {
  ui = {
    erzeugen: el('button', { type: 'button', className: 'primaer', textContent: 'Antwortentwurf erzeugen' }),
    stopp:    el('button', { type: 'button', className: 'stopp', textContent: '■ Stopp', disabled: true }),
    zustand:  el('span', { id: 'zustand', textContent: 'bereit' }),
    vorschlag: el('div', { id: 'vorschlag' }),
    begruendung: el('p', { id: 'begruendung' }),
    entwurf:  el('textarea', { id: 'entwurf', placeholder: 'Antwortentwurf erscheint hier — Wort für Wort.', readOnly: true }),
    hinweis:  el('span', { id: 'entwurf-hinweis' }),
    aktionen: el('div', { id: 'aktionen' }),
    antwort:  el('textarea', { id: 'antwort', placeholder: 'Ihre Antwort an den Kunden' }),
    senden:   el('button', { type: 'button', className: 'primaer', textContent: 'Senden …', disabled: true }),
    meldung:  el('div', { id: 'meldung' }),
  }
  ui.zustand.dataset.zustand = 'bereit'
  ui.erzeugen.addEventListener('click', erzeugen)
  ui.stopp.addEventListener('click', stoppen)
  ui.senden.addEventListener('click', senden)
  ui.antwort.addEventListener('input', () => { ui.senden.disabled = ui.antwort.value.trim() === '' })
  const kopf = el('div', { className: 'kopf' }, ui.erzeugen, ui.stopp, ui.zustand)
  const entwurfKopf = el('div', { className: 'kopf' }, el('span', { textContent: 'Antwortentwurf' }), ui.hinweis)
  const antwortKopf = el('div', { className: 'kopf' }, el('span', { textContent: 'Ihre Antwort' }), ui.senden)
  const box = el('section', { id: 'assistent' },
    el('h3', { textContent: 'Assistent', style: 'margin:0;font-size:1rem' }),
    kopf, ui.vorschlag, ui.begruendung, entwurfKopf, ui.entwurf, ui.aktionen, antwortKopf, ui.antwort, ui.meldung)
  box.setAttribute('aria-label', 'Assistent')
  platz.replaceChildren(box)
}

function setzeZustand(z) {                         // ② jeder Zustand sichtbar
  ui.zustand.textContent = z
  ui.zustand.dataset.zustand = z
  const laeuft = z === 'wartet' || z === 'strömt'
  ui.erzeugen.disabled = laeuft
  ui.stopp.disabled = !laeuft
  const unvollstaendig = z === 'abgebrochen' || z === 'fehler'
  ui.entwurf.classList.toggle('teilantwort', unvollstaendig)
  ui.hinweis.textContent = unvollstaendig ? '[unvollständig]' : (z === 'fertig' ? 'Antwortentwurf — noch nichts gesendet' : '')
}

function hinweis(text, fehler = false) {
  ui.meldung.replaceChildren()
  if (!text) return
  const box = el('div', { className: 'meldung klein', textContent: text })
  if (fehler) box.setAttribute('role', 'alert')
  ui.meldung.replaceChildren(box)
}

async function erzeugen() {
  stoppen(true)
  ui.vorschlag.replaceChildren(); ui.begruendung.textContent = ''; ui.aktionen.replaceChildren()
  ui.entwurf.value = ''; hinweis('')
  setzeZustand('wartet')
  abbruch = new AbortController()
  const signal = abbruch.signal
  einschaetzung(signal)                            // parallel: JSON am Stück
  await entwurf(signal)                            // der Strom
}

async function einschaetzung(signal) {
  try {
    const r = await fetch(`/api/suggest?${apiParams()}`, { signal })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    zeigeEinschaetzung(await r.json())
  } catch (e) {
    if (e.name !== 'AbortError') hinweis('Einschätzung nicht verfügbar.', true)
  }
}

function zeigeEinschaetzung(s) {                   // ③ Struktur ist auch nur LLM-Text: prüfen, dann rendern
  const chips = []
  if (typeof s.kategorie === 'string' && s.kategorie) chips.push(vorschlagChip('Kategorie', s.kategorie))
  if (['tief', 'mittel', 'hoch'].includes(s.prioritaet)) chips.push(vorschlagChip('Priorität', s.prioritaet))
  ui.vorschlag.replaceChildren(el('span', { textContent: 'Vorschlag', style: 'color:var(--fg-schwach)' }), ...chips)
  ui.begruendung.textContent = typeof s.begruendung === 'string' ? s.begruendung : ''   // Text, nie HTML
  const knoepfe = (Array.isArray(s.aktionen) ? s.aktionen : [])
    .filter(a => a in ERLAUBT)                     // unbekannt («gutschrift») → kein Element, auch nicht ausgegraut
    .map(a => aktionKnopf(a))
  ui.aktionen.replaceChildren(...knoepfe)
}

function vorschlagChip(label, wert) {              // autonom: ein Klick übernimmt, ein zweiter nimmt zurück
  const b = el('button', { type: 'button', className: 'chip chip-vorschlag', textContent: `${label}: ${wert}` })
  b.setAttribute('aria-pressed', 'false')
  b.addEventListener('click', () => b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') === 'true' ? 'false' : 'true'))
  return b
}

function aktionKnopf(a) {
  const { text, stufe } = ERLAUBT[a]
  const b = el('button', { type: 'button', textContent: text })
  b.dataset.aktion = a
  b.addEventListener('click', () => {
    if (stufe === 'autonom') {                     // «antworten»: Entwurf ins Antwortfeld — nichts geht raus
      ui.antwort.value = ui.entwurf.value
      ui.senden.disabled = ui.antwort.value.trim() === ''
      ui.antwort.focus()
      return
    }
    if (window.confirm(`${text.replace(' …', '')} — Ticket #${ticket.id}?`)) hinweis(`${text.replace(' …', '')}: ausgelöst (simuliert).`)
  })
  return b
}

async function entwurf(signal) {
  const timer = setTimeout(() => abbruch?.abort('timeout'), TIMEOUT_MS)
  try {
    const r = await fetch(`/api/draft?${apiParams()}`, { signal })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const leser = r.body.getReader()
    const dec = new TextDecoder()
    let puffer = ''
    while (true) {
      const { value, done } = await leser.read()
      clearTimeout(timer)
      if (done) break
      puffer += dec.decode(value, { stream: true })
      let i
      while ((i = puffer.indexOf('\n\n')) >= 0) {
        const ereignis = puffer.slice(0, i); puffer = puffer.slice(i + 2)
        const typ = (ereignis.match(/^event: (.*)$/m) || [, 'message'])[1]
        const data = (ereignis.match(/^data: (.*)$/m) || [, ''])[1]
        if (typ === 'done') { setzeZustand('fertig'); return }
        if (typ === 'error') { setzeZustand('fehler'); hinweis(`Service meldet: ${data}`, true); return }
        setzeZustand('strömt')
        ui.entwurf.value += (ui.entwurf.value ? ' ' : '') + data     // Text, nie HTML
      }
    }
    setzeZustand(ui.entwurf.value ? 'fertig' : 'fehler')
  } catch (e) {
    clearTimeout(timer)
    if (e.name === 'AbortError' && signal.reason !== 'timeout') { setzeZustand('abgebrochen'); return }
    setzeZustand('fehler')
    hinweis(signal.reason === 'timeout' ? 'Service antwortet nicht. Das Ticket bleibt bearbeitbar.' : 'Service nicht erreichbar. Das Ticket bleibt bearbeitbar.', true)
  }
}

function stoppen(still = false) {                  // ④ Stopp schliesst die Verbindung — der Mock meldet «Abbruch bemerkt»
  if (!abbruch) return
  abbruch.abort()
  abbruch = null
  if (!still) setzeZustand('abgebrochen')
}

function senden() {                                // ⑤ nur per Klick, mit Rückfrage — nie automatisch
  if (!window.confirm(`Antwort an den Kunden von Ticket #${ticket.id} senden?`)) return
  hinweis('Gesendet (simuliert). Ticket bleibt offen, bis der Service es bestätigt.')
  ui.senden.disabled = true
}

document.addEventListener('ticket:geladen', ev => {
  stoppen(true)
  ticket = ev.detail
  const platz = document.getElementById('assistent-platz')
  if (platz) baue(platz)
})
