const { test, expect } = require('@playwright/test')
const vorschlag = { kategorie: 'Account', prioritaet: 'hoch', aktionen: ['antworten'], begruendung: 'Blockiert.' }
const strom = 'data: Hallo\n\nevent: done\ndata: {}\n\n'
async function start(page) {
  await page.goto('/posteingang.html?id=409')
  await page.getByRole('button', { name: 'Antwortentwurf erzeugen' }).click()
}
test('lokal: später Entwurf und Einschätzung überleben die bisherigen fünf Sekunden', async ({ page }) => {
  await page.route('**/api/suggest?*', async r => {
    await new Promise(resolve => setTimeout(resolve, 6500))
    await r.fulfill({ json: vorschlag })
  })
  await page.route('**/api/draft?*', async r => {
    await new Promise(resolve => setTimeout(resolve, 5500))
    await r.fulfill({ contentType: 'text/event-stream', body: strom })
  })
  await start(page)
  await expect(page.locator('#einschaetzung-zustand')).toContainText('lädt')
  await expect(page.locator('#vorschlag')).toContainText('Priorität: hoch', { timeout: 10000 })
  await expect(page.locator('#zustand')).toHaveText('fertig')
})
test('lokal: Entwurffehler bricht Einschätzung nicht ab', async ({ page }) => {
  await page.route('**/api/draft?*', r => r.fulfill({ status: 503, json: { meldung: 'Prüfung abgewiesen' } }))
  await page.route('**/api/suggest?*', async r => {
    await new Promise(resolve => setTimeout(resolve, 700))
    await r.fulfill({ json: vorschlag })
  })
  await start(page)
  await expect(page.locator('#zustand')).toHaveText('fehler')
  await expect(page.locator('#vorschlag')).toContainText('Priorität: hoch')
  await expect(page.locator('#entwurf')).toHaveValue('')
})
test('lokal: Einschätzungsfehler verhindert Entwurf nicht', async ({ page }) => {
  await page.route('**/api/suggest?*', r => r.fulfill({ status: 503, json: {} }))
  await page.route('**/api/draft?*', r => r.fulfill({ contentType: 'text/event-stream', body: strom }))
  await start(page)
  await expect(page.locator('#zustand')).toHaveText('fertig')
  await expect(page.locator('#einschaetzung-zustand')).toContainText('nicht verfügbar')
})
test('lokal: Stopp verwirft verspätete Antworten', async ({ page }) => {
  for (const pfad of ['suggest', 'draft']) {
    await page.route(`**/api/${pfad}?*`, async r => {
      await new Promise(resolve => setTimeout(resolve, 1200))
      await r.fulfill(pfad === 'suggest' ? { json: vorschlag } : { contentType: 'text/event-stream', body: strom }).catch(() => {})
    })
  }
  await start(page)
  await page.getByRole('button', { name: '■ Stopp' }).click()
  await page.waitForTimeout(1500)
  await expect(page.locator('#zustand')).toHaveText('abgebrochen')
  await expect(page.locator('#entwurf')).toHaveValue('')
  await expect(page.locator('#vorschlag')).toBeEmpty()
})
