// Statusübersicht — ein Test je Verhalten. Der Mock-Service muss laufen (./mock.sh),
// die Antwort von /api/tickets wird je Test gestellt.
const { test, expect } = require('@playwright/test')

const TICKETS = [
  { id: 1, titel: 'Rechnung doppelt belastet', status: 'eskaliert', prio: 'hoch', text: '…' },
  { id: 2, titel: 'Login geht nicht mehr', status: 'offen', prio: 'mittel', text: '…' },
  { id: 3, titel: '<img src=x onerror="alert(1)">', status: 'eskaliert', prio: 'tief', text: '…' },
  { id: 4, titel: 'Passwort zurückgesetzt', status: 'erledigt', prio: 'tief', text: '…' },
]

async function stelleTickets(page, tickets) {
  await page.route('**/api/tickets', route => route.fulfill({ json: tickets }))
}

test('zählt Tickets je Status', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/')
  await expect(page.locator('.kachel[data-status=offen] .zahl')).toHaveText('1')
  await expect(page.locator('.kachel[data-status=eskaliert] .zahl')).toHaveText('2')
  await expect(page.locator('.kachel[data-status=erledigt] .zahl')).toHaveText('1')
})

test('listet eskalierte Tickets als Links, Kundentext nur angezeigt', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/')
  const zeilen = page.locator('#eskaliert a.zeile')
  await expect(zeilen).toHaveCount(2)
  await expect(zeilen.first()).toHaveAttribute('href', '/posteingang.html?id=1')
  await expect(zeilen.first()).toContainText('Rechnung doppelt belastet')
  await expect(zeilen.nth(1).locator('.titel')).toHaveText('<img src=x onerror="alert(1)">')
  await expect(page.locator('#eskaliert img')).toHaveCount(0)
})

test('Kachel «eskaliert 3» und darunter drei Zeilen', async ({ page }) => {
  await stelleTickets(page, [
    { id: 11, titel: 'Zahlung nicht verbucht', status: 'eskaliert', prio: 'hoch', text: '…' },
    { id: 12, titel: 'Konto gesperrt', status: 'eskaliert', prio: 'hoch', text: '…' },
    { id: 13, titel: 'Export bricht ab', status: 'eskaliert', prio: 'mittel', text: '…' },
    { id: 14, titel: 'Adresse geändert', status: 'offen', prio: 'tief', text: '…' },
  ])
  await page.goto('/')
  const kachel = page.locator('.kachel[data-status=eskaliert]')
  await expect(kachel.locator('.chip')).toHaveText('eskaliert')
  await expect(kachel.locator('.zahl')).toHaveText('3')
  const zeilen = page.locator('#eskaliert a.zeile')
  await expect(zeilen).toHaveCount(3)
  await expect(zeilen).toHaveText([/#11.*Zahlung nicht verbucht.*hoch/,
                                   /#12.*Konto gesperrt.*hoch/,
                                   /#13.*Export bricht ab.*mittel/])
  // Die Liste steht unterhalb der Kacheln.
  const kachelUnten = (await kachel.boundingBox()).y + (await kachel.boundingBox()).height
  expect((await zeilen.first().boundingBox()).y).toBeGreaterThan(kachelUnten)
})

test('zeigt den Leerfall', async ({ page }) => {
  await stelleTickets(page, [])
  await page.goto('/')
  await expect(page.locator('#eskaliert')).toContainText('Keine eskalierten Tickets.')
  await expect(page.locator('.kachel[data-status=offen] .zahl')).toHaveText('0')
})

test('zeigt den Ausfall des Service und lädt per Knopf erneut', async ({ page }) => {
  let ausfall = true
  await page.route('**/api/tickets', route =>
    ausfall ? route.abort('connectionrefused') : route.fulfill({ json: TICKETS }))
  await page.goto('/')
  const meldung = page.getByRole('alert')
  await expect(meldung).toContainText('Ticket-Service nicht erreichbar')
  await expect(page.locator('.kachel[data-status=offen] .zahl')).toHaveText('–')
  ausfall = false
  await page.getByRole('button', { name: 'Erneut laden' }).focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('#eskaliert a.zeile')).toHaveCount(2)
})

test('Zeile ist per Tab erreichbar und öffnet mit Enter das Ticket', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/')
  await page.locator('#eskaliert a.zeile').first().waitFor()
  await page.keyboard.press('Tab')
  await expect(page.locator('#eskaliert a.zeile').first()).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/posteingang\.html\?id=1$/)
})

test('in der Liste wechseln Pfeil ab und auf die Zeile, Enter öffnet', async ({ page }) => {
  await stelleTickets(page, TICKETS)
  await page.goto('/')
  const zeilen = page.locator('#eskaliert a.zeile')
  await zeilen.first().focus()
  await page.keyboard.press('ArrowDown')
  await expect(zeilen.nth(1)).toBeFocused()
  await page.keyboard.press('ArrowDown')          // am Ende: bleibt stehen
  await expect(zeilen.nth(1)).toBeFocused()
  await page.keyboard.press('ArrowUp')
  await expect(zeilen.first()).toBeFocused()
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/posteingang\.html\?id=3$/)
})
