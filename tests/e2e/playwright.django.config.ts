import { join } from 'node:path';
import { defineConfig, devices } from '@playwright/test';

/**
 * The final stage of the real-tools end-to-end flow: Django alone serves the built Angular
 * application (`django_angular3.spa`), as in the production-like topology of
 * `doc/specifications/SPECIFICATIONS.md` section 5.1. There is no Angular dev server and no
 * proxy: the browser talks to one origin for the pages, the assets and the API.
 *
 * `tests/e2e/run_e2e.py` (stage 6b) starts this configuration. It runs the specs of the
 * dev-server run against that origin and adds `django-served.spec.ts`.
 */
function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is not set; run the flow with: DJNG_E2E=1 python -m tests.e2e.run_e2e`);
  }
  return value;
}

const python = required('E2E_PYTHON');
const projectDir = required('E2E_PROJECT_DIR');
const evidenceDir = required('E2E_EVIDENCE_DIR');
const djangoUrl = required('E2E_DJANGO_URL');
const djangoPort = new URL(djangoUrl).port;
const chromiumPath = process.env['E2E_CHROMIUM_PATH'];

export default defineConfig({
  testDir: './specs',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env['CI'],
  outputDir: join(evidenceDir, 'playwright-django-results'),
  reporter: [
    ['list'],
    ['html', { outputFolder: join(evidenceDir, 'playwright-django-report'), open: 'never' }],
    ['json', { outputFile: join(evidenceDir, 'playwright-django-results.json') }],
  ],
  use: {
    baseURL: djangoUrl,
    trace: 'on',
    screenshot: 'on',
    launchOptions: chromiumPath ? { executablePath: chromiumPath } : {},
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `"${python}" manage.py runserver 127.0.0.1:${djangoPort} --noreload`,
    cwd: projectDir,
    url: `${djangoUrl}/api/v1/products/`,
    timeout: 60_000,
    reuseExistingServer: false,
    env: { DJANGO_SETTINGS_MODULE: required('E2E_SETTINGS_MODULE') },
  },
});
