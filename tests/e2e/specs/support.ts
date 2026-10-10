import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Page } from '@playwright/test';

export interface SeedCustomer {
  name: string;
  email: string;
  phone: string;
  active: boolean;
}

export const djangoUrl = process.env['E2E_DJANGO_URL'] ?? 'http://127.0.0.1:8000';
export const evidenceDir = process.env['E2E_EVIDENCE_DIR'] ?? '.';
export const PAGE_SIZE = 10;

/** The test user the flow creates in the tutorial project's database (stage 1). */
export const credentials = {
  username: process.env['E2E_USERNAME'] ?? '',
  password: process.env['E2E_PASSWORD'] ?? '',
};

/** The customers of the committed seed fixture, in primary-key order (the API order). */
export function seedCustomers(): SeedCustomer[] {
  const documents = JSON.parse(readFileSync(process.env['E2E_SEED'] ?? '', 'utf8')) as {
    model: string;
    pk: number;
    fields: SeedCustomer;
  }[];
  return documents
    .filter((document) => document.model === 'shop.customer')
    .sort((a, b) => a.pk - b.pk)
    .map((document) => document.fields);
}

/** Where the screenshots go; the Django-served run keeps its own set (`screenshots-django`). */
export const screenshotDirectory = process.env['E2E_SCREENSHOT_DIR'] ?? 'screenshots';

export function screenshotPath(name: string): string {
  return join(evidenceDir, screenshotDirectory, `${name}.png`);
}

/** Records the console errors and uncaught page errors of a page. */
export function collectErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      errors.push(message.text());
    }
  });
  page.on('pageerror', (error) => errors.push(error.message));
  return errors;
}

/** True for a GET of the customers list at the given page number. */
export function isCustomersPage(url: string, pageNumber: number): boolean {
  const parsed = new URL(url);
  return (
    parsed.pathname === '/api/v1/customers/' && parsed.searchParams.get('page') === String(pageNumber)
  );
}
