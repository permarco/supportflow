// Playwright-Konfiguration. Auf Port 8765 muss ein Service laufen: ./service.sh (oder zum Vergleich ./mock.sh)
// Tests liegen unter tests/ — ein Test je Verhalten.
module.exports = {
  testDir: './tests',
  timeout: 20_000,
  use: {
    baseURL: 'http://localhost:8765',
    headless: true,
  },
  reporter: 'list',
};
