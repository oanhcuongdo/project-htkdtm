import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, devices } from '@playwright/test'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function loadEnvFile(envPath: string) {
  if (!fs.existsSync(envPath)) return
  const content = fs.readFileSync(envPath, 'utf8')
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const eqIdx = line.indexOf('=')
    if (eqIdx <= 0) continue
    const key = line.slice(0, eqIdx).trim()
    let val = line.slice(eqIdx + 1).trim()
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1)
    }
    process.env[key] ??= val
  }
}

loadEnvFile(path.resolve(__dirname, '../.env'))

const e2eApiUrl = process.env.NEXT_PUBLIC_API_URL ?? process.env.VITE_API_URL ?? process.env.E2E_API_BASE ?? 'http://localhost:8000/api/v1'
const e2eWebBase = process.env.E2E_WEB_BASE ?? 'http://localhost:3000'
const e2eWebUrl = new URL(e2eWebBase)
const webServerCommand = process.platform === 'win32'
  ? `set NEXT_PUBLIC_API_URL=${e2eApiUrl}&& npm.cmd run dev -- --hostname ${e2eWebUrl.hostname} --port ${e2eWebUrl.port || '3000'}`
  : `NEXT_PUBLIC_API_URL=${e2eApiUrl} npm run dev -- --hostname ${e2eWebUrl.hostname} --port ${e2eWebUrl.port || '3000'}`

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 1,
  timeout: 60000,
  globalSetup: path.resolve(__dirname, 'e2e', 'global-setup.ts'),
  globalTeardown: path.resolve(__dirname, 'e2e', 'global-teardown.ts'),
  reporter: [
    ['list'],
    ['html', { outputFolder: 'e2e/reports' }]
  ],
  use: {
    baseURL: e2eWebBase,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: webServerCommand,
    url: e2eWebBase,
    reuseExistingServer: true,
    timeout: 120000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: ['--no-sandbox', '--disable-setuid-sandbox']
        }
      }
    }
  ]
})
