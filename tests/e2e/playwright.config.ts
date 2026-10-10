import { join } from 'node:path';
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright side of the real-tools end-to-end flow. `tests/e2e/run_e2e.py` creates the
 * project and the Angular workspace, then starts this configuration with the paths below.
 * Both servers are real: Django's `runserver` and the Angular dev server, which proxies
 * `/api` to Django (`proxy.conf.json`), so the browser sees one origin.
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
const workspaceDir = required('E2E_WORKSPACE_DIR');
const applicationName = required('E2E_APPLICATION');
const evidenceDir = required('E2E_EVIDENCE_DIR');
const djangoUrl = required('E2E_DJANGO_URL');
const angularUrl = required('E2E_ANGULAR_URL');
const djangoPort = new URL(djangoUrl).port;
const angularPort = new URL(angularUrl).port;
const chromiumPath = process.env['E2E_CHROMIUM_PATH'];

export default defineConfig({
  testDir: './specs',
  // The Django-served run (playwright.django.config.ts) adds django-served.spec.ts.
  testIgnore: '**/django-served.spec.ts',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env['CI'],
  outputDir: join(evidenceDir, 'playwright-results'),
  reporter: [
    ['list'],
    ['html', { outputFolder: join(evidenceDir, 'playwright-report'), open: 'never' }],
    ['json', { outputFile: join(evidenceDir, 'playwright-results.json') }],
  ],
  use: {
    baseURL: angularUrl,
    trace: 'on',
    screenshot: 'on',
    launchOptions: chromiumPath ? { executablePath: chromiumPath } : {},
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `"${python}" manage.py runserver 127.0.0.1:${djangoPort} --noreload`,
      cwd: projectDir,
      url: `${djangoUrl}/api/v1/products/`,
      timeout: 60_000,
      reuseExistingServer: false,
      env: { DJANGO_SETTINGS_MODULE: required('E2E_SETTINGS_MODULE') },
    },
    {
      command: `ng serve ${applicationName} --proxy-config proxy.conf.json --host 127.0.0.1 --port ${angularPort}`,
      cwd: workspaceDir,
      url: angularUrl,
      timeout: 300_000,
      reuseExistingServer: false,
    },
  ],
});
