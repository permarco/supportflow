// Posteingang — ein Test je Verhalten. Der Mock-Service muss laufen (./mock.sh),
// die Antworten von /api/tickets und /api/tickets/<id> werden je Test gestellt.
const { test, expect } = require('@playwright/test')

const TICKETS = [
  { id: 409, titel: 'Login schlägt fehl', status: 'eskaliert', prio: 'hoch',
    text: 'Seit dem Update kann ich mich nicht mehr anmelden.' },
  { id: 412, titel: 'Rechnung doppelt erhalten', status: 'offen', prio: 'hoch', text: 'Welche Rechnung gilt?' },
  { id: 422, titel: 'Kunde schreibt <b>test</b>', status: 'eskaliert', prio: 'tief',
    text: 'Hallo, <b>test</b> — kommt das <script>alert(1)</script> an?' },
  { id: 425, titel: 'Rückerstattung gefordert', status: 'eskaliert', prio: 'hoch', text: 'Ich will mein Geld zurück.' },
]

async function stelleTickets(page, tickets) {
  await page.route('**/api/tickets', route => route.fulfill({ json: tickets }))
  await page.route('**/api/tickets/*', route => {
    const id = Number(route.request().url().split('/').pop())
    const t = tickets.find(t => t.id === id)
    return t ? route.fulfill({ json: t }) : route.fulfill({ status: 404, json: { fehler: `Ticket ${id} unbekannt` } })
  })
}

test('listet alle Tickets, Filter «eskaliert» steht in der Adresse und zeigt nur eskalierte', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/posteingang.html')
  await expect(page.locator('#liste a.zeile')).toHaveCount(4)
  await expect(page.locator('#detail')).toContainText('Wählen Sie links ein Ticket.')
  await page.getByRole('button', { name: 'eskaliert' }).click()
  await expect(page).toHaveURL(/\?status=eskaliert$/)
  await expect(page.locator('#liste a.zeile')).toHaveText([/#409/, /#422/, /#425/])
  await expect(page.getByRole('button', { name: 'eskaliert' })).toHaveAttribute('aria-pressed', 'true')
})

test('Ticket 409 in der Adresse: das Detail zeigt «#409 · Login schlägt fehl»', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/posteingang.html?id=409')
  await expect(page.locator('#detail h2')).toHaveText('#409 · Login schlägt fehl')
  await expect(page.locator('#detail .chip')).toHaveText('eskaliert')
  await expect(page.locator('#detail .text')).toContainText('Seit dem Update')
  await expect(page.locator('#liste a.zeile[aria-current]')).toContainText('#409')
})

test('Klick auf eine Zeile wechselt Auswahl und Adresse, der Filter bleibt stehen', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/posteingang.html?status=eskaliert&id=409')
  await page.locator('#liste a.zeile', { hasText: '#425' }).click()
  await expect(page).toHaveURL(/\?status=eskaliert&id=425$/)
  await expect(page.locator('#detail h2')).toHaveText('#425 · Rückerstattung gefordert')
  await expect(page.locator('#liste a.zeile')).toHaveCount(3)
})

test('der Zurück-Knopf des Browsers führt zum vorherigen Ticket', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/posteingang.html?id=409')
  await page.locator('#liste a.zeile', { hasText: '#412' }).click()
  await expect(page.locator('#detail h2')).toHaveText('#412 · Rechnung doppelt erhalten')
  await page.goBack()
  await expect(page).toHaveURL(/\?id=409$/)
  await expect(page.locator('#detail h2')).toHaveText('#409 · Login schlägt fehl')
  await expect(page.locator('#liste a.zeile[aria-current]')).toContainText('#409')
})

test('Kundentext wird als Zeichen angezeigt, nie als HTML ausgeführt', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/posteingang.html?id=422')
  await expect(page.locator('#liste a.zeile', { hasText: '#422' }).locator('.titel')).toHaveText('Kunde schreibt <b>test</b>')
  await expect(page.locator('#detail h2')).toHaveText('#422 · Kunde schreibt <b>test</b>')
  await expect(page.locator('#detail .text')).toContainText('<script>alert(1)</script>')
  await expect(page.locator('#liste b, #detail b, #detail script')).toHaveCount(0)
})

test('Tastatur: Tab in die Liste, Pfeil ab wechselt die Zeile, Enter öffnet', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/posteingang.html')
  const zeilen = page.locator('#liste a.zeile')
  await zeilen.first().waitFor()
  await page.getByRole('button', { name: 'erledigt' }).focus()   // letzter Filter-Knopf
  await page.keyboard.press('Tab')
  await expect(zeilen.first()).toBeFocused()
  await page.keyboard.press('ArrowDown')
  await expect(zeilen.nth(1)).toBeFocused()
  await page.keyboard.press('ArrowUp')
  await expect(zeilen.first()).toBeFocused()
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\?id=412$/)
  await expect(page.locator('#detail h2')).toHaveText('#412 · Rechnung doppelt erhalten')
  await expect(zeilen.nth(1)).toBeFocused()   // der Fokus bleibt in der Liste
})

test('Leerfall: kein Ticket im Filter, unbekannte Nummer in der Adresse', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/posteingang.html?status=erledigt&id=999')
  await expect(page.locator('#liste')).toContainText('Keine Tickets mit Status «erledigt».')
  await expect(page.locator('#detail')).toContainText('Ticket #999 gibt es nicht.')
})

test('Ausfall des Service: Meldung, und «Erneut laden» holt die Liste', async ({ page }) => {
  let ausfall = true
  await page.route('**/api/tickets', route =>
    ausfall ? route.abort('connectionrefused') : route.fulfill({ json: TICKETS }))
  await page.route('**/api/tickets/*', route => route.fulfill({ json: TICKETS[0] }))
  await page.goto('/posteingang.html?id=409')
  await expect(page.getByRole('alert')).toContainText('Ticket-Service nicht erreichbar')
  await expect(page.locator('#liste a.zeile')).toHaveCount(0)
  ausfall = false
  await page.getByRole('button', { name: 'Erneut laden' }).focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('#liste a.zeile')).toHaveCount(4)
  await expect(page.locator('#detail h2')).toHaveText('#409 · Login schlägt fehl')
})
