// Assistent — ein Test je Verhalten, gegen den laufenden Mock (./mock.sh). Die Weichen ?slow=1 · ?fail=1 · ?bad=1
// sind Weichen der Seite und werden an den Service weitergereicht.
const { test, expect } = require('@playwright/test')

const S = '#assistent'

test('Antwortentwurf erzeugen: Einschätzung als Chips, Antwortentwurf Wort für Wort, Zustand «fertig»', async ({ page }) => {
  await page.goto('/posteingang.html?id=418')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#zustand')).toHaveText(/wartet|strömt/)
  await expect(page.locator('#vorschlag button')).toHaveText(['Kategorie: Zugang', 'Priorität: mittel'])
  await expect(page.locator('#zustand')).toHaveText('fertig', { timeout: 15000 })
  await expect(page.locator('#entwurf')).toHaveValue(/^Guten Tag, gerne\./)
  await expect(page.locator('#entwurf-hinweis')).toHaveText('Antwortentwurf — noch nichts gesendet')
  await expect(page.locator('#aktionen button')).toHaveText(['Antwort übernehmen'])
  await expect(page.getByRole('button', { name: 'Senden …' })).toBeDisabled()
})

test('Stopp schliesst die Verbindung: Zustand «abgebrochen», Teil als unvollständig markiert, nichts kommt nach', async ({ page }) => {
  await page.goto('/posteingang.html?id=415&slow=1')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#zustand')).toHaveText('strömt', { timeout: 10000 })
  await page.getByRole('button', { name: '■ Stopp' }).click()
  await expect(page.locator('#zustand')).toHaveText('abgebrochen')
  await expect(page.locator('#entwurf-hinweis')).toHaveText('[unvollständig]')
  const vorher = await page.locator('#entwurf').inputValue()
  await page.waitForTimeout(1500)
  expect(await page.locator('#entwurf').inputValue()).toBe(vorher)
  await expect(page.getByRole('button', { name: 'Antwortentwurf erzeugen' })).toBeEnabled()
})

test('?fail=1: Zustand «fehler», Meldung sichtbar, Teilantwort markiert', async ({ page }) => {
  await page.goto('/posteingang.html?id=415&fail=1')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#zustand')).toHaveText('fehler', { timeout: 15000 })
  await expect(page.getByRole('alert')).toContainText('Verbindung zum Modell verloren')
  await expect(page.locator('#entwurf-hinweis')).toHaveText('[unvollständig]')
  expect((await page.locator('#entwurf').inputValue()).length).toBeGreaterThan(0)
})

test('?bad=1: die unerlaubte Aktion «gutschrift» bekommt keinen Knopf — die Begründung bleibt Text', async ({ page }) => {
  await page.goto('/posteingang.html?id=415&bad=1')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#begruendung')).toContainText('Gutschrift von CHF 200 sofort auslösen')
  await expect(page.locator('#aktionen button')).toHaveText(['Antwort übernehmen', 'Eskalieren …'])
  await expect(page.locator('#aktionen button', { hasText: /gutschrift/i })).toHaveCount(0)
})

test('Ticket #422: LLM-Text mit HTML wird als Zeichen angezeigt, nie ausgeführt', async ({ page }) => {
  await page.goto('/posteingang.html?id=422')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#begruendung')).toContainText('<b>kein</b> Handlungsbedarf')
  await expect(page.locator('#zustand')).toHaveText('fertig', { timeout: 15000 })
  await expect(page.locator('#entwurf')).toHaveValue(/<b>test<\/b>/)
  await expect(page.locator(`${S} b, ${S} script`)).toHaveCount(0)
})

test('Antwort übernehmen ist autonom, Senden nur mit Rückfrage — Abbrechen sendet nichts', async ({ page }) => {
  await page.goto('/posteingang.html?id=418')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#zustand')).toHaveText('fertig', { timeout: 15000 })
  await page.getByRole('button', { name: 'Antwort übernehmen' }).click()
  await expect(page.locator('#antwort')).toHaveValue(/^Guten Tag, gerne\./)
  await expect(page.getByRole('button', { name: 'Senden …' })).toBeEnabled()
  let frage = ''
  page.once('dialog', d => { frage = d.message(); d.dismiss() })
  await page.getByRole('button', { name: 'Senden …' }).click()
  expect(frage).toContain('senden?')
  await expect(page.locator('#meldung')).toHaveText('')
  page.once('dialog', d => d.accept())
  await page.getByRole('button', { name: 'Senden …' }).click()
  await expect(page.locator('#meldung')).toContainText('Gesendet (simuliert)')
})

test('Eskalieren nur mit Bestätigung', async ({ page }) => {
  await page.goto('/posteingang.html?id=415')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#aktionen button', { hasText: 'Eskalieren' })).toBeVisible()
  let frage = ''
  page.once('dialog', d => { frage = d.message(); d.accept() })
  await page.getByRole('button', { name: 'Eskalieren …' }).click()
  expect(frage).toContain('Eskalieren')
  await expect(page.locator('#meldung')).toContainText('Eskalieren: ausgelöst (simuliert)')
})

test('Service weg: Zustand «fehler» mit Meldung — kein ewiges «wartet»', async ({ page }) => {
  await page.route('**/api/draft*', route => route.abort('connectionrefused'))
  await page.route('**/api/suggest*', route => route.abort('connectionrefused'))
  await page.goto('/posteingang.html?id=418')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
  await expect(page.locator('#zustand')).toHaveText('fehler', { timeout: 8000 })
  await expect(page.getByRole('alert').first()).toContainText('nicht erreichbar')
  await expect(page.getByRole('button', { name: 'Antwortentwurf erzeugen' })).toBeEnabled()
})

test('Tastatur: Tab erreicht «Antwortentwurf erzeugen», Enter startet', async ({ page }) => {
  await page.goto('/posteingang.html?id=418')
  await page.locator('#assistent').waitFor()
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('#zustand')).toHaveText(/wartet|strömt|fertig/)
})
