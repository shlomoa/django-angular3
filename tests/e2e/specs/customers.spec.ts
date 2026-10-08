import { expect, test, type Page } from '@playwright/test';

import {
  collectErrors,
  djangoUrl,
  isCustomersPage,
  PAGE_SIZE,
  screenshotPath,
  seedCustomers,
} from './support';

const customerNames = (page: Page) => page.locator('td.mat-column-name');
const nextPage = (page: Page) => page.getByRole('button', { name: 'Next page' });

function customersResponse(page: Page, pageNumber: number) {
  return page.waitForResponse(
    (response) =>
      response.request().method() === 'GET' && isCustomersPage(response.url(), pageNumber),
  );
}

test.describe('customers page against the real Django backend', () => {
  test('P1 shell: the app loads and the navigation lists Customers and Products', async ({
    page,
  }) => {
    const errors = collectErrors(page);

    await page.goto('/');
    const links = page.locator('mat-sidenav a[mat-list-item]');
    await expect(links).toHaveText([/Home/, /Customers/, /Products/]);
    await expect(links.nth(1)).toHaveAttribute('href', '/customers');
    await expect(links.nth(2)).toHaveAttribute('href', '/products');
    await page.screenshot({ path: screenshotPath('P1-shell') });

    await links.nth(1).click();
    await expect(page).toHaveURL(/\/customers$/);
    await expect(page.getByText('Customers').first()).toBeVisible();

    expect(errors, 'console and page errors').toEqual([]);
  });

  test('P2 data alignment: the table shows the first page of the real API', async ({
    page,
    request,
  }) => {
    const seed = seedCustomers();
    const [response] = await Promise.all([customersResponse(page, 1), page.goto('/customers')]);

    expect(response.status()).toBe(200);
    const body = (await response.json()) as {
      count: number;
      results: { name: string; email: string }[];
    };
    expect(body.count).toBe(seed.length);

    await expect(customerNames(page)).toHaveCount(PAGE_SIZE);
    const expected = seed.slice(0, PAGE_SIZE).map((customer) => customer.name);
    await expect(customerNames(page)).toHaveText(expected);
    await expect(page.locator('td.mat-column-email')).toHaveText(
      seed.slice(0, PAGE_SIZE).map((customer) => customer.email),
    );

    // The proxied response, a direct call to Django and the seed agree.
    expect(body.results.map((customer) => customer.name)).toEqual(expected);
    const direct = await request.get(`${djangoUrl}/api/v1/customers/?page=1`);
    expect(direct.status()).toBe(200);
    expect(((await direct.json()) as { results: unknown[] }).results).toEqual(body.results);
    await page.screenshot({ path: screenshotPath('P2-data-alignment') });
  });

  test('P3 pagination: next page requests ?page=2 and the last page has the remainder', async ({
    page,
  }) => {
    const seed = seedCustomers();
    await page.goto('/customers');
    await expect(customerNames(page)).toHaveCount(PAGE_SIZE);

    const [second] = await Promise.all([customersResponse(page, 2), nextPage(page).click()]);
    expect(second.status()).toBe(200);
    await expect(customerNames(page)).toHaveText(
      seed.slice(PAGE_SIZE, 2 * PAGE_SIZE).map((customer) => customer.name),
    );
    await page.screenshot({ path: screenshotPath('P3-page-2') });

    const [third] = await Promise.all([customersResponse(page, 3), nextPage(page).click()]);
    expect(third.status()).toBe(200);
    await expect(customerNames(page)).toHaveCount(seed.length - 2 * PAGE_SIZE);
    await expect(customerNames(page)).toHaveText(
      seed.slice(2 * PAGE_SIZE).map((customer) => customer.name),
    );
    await expect(nextPage(page)).toBeDisabled();
    await page.screenshot({ path: screenshotPath('P3-last-page') });
  });

  for (const [label, fulfil] of [
    ['an aborted request', 'abort'],
    ['a server error', 'error'],
  ] as const) {
    test(`P4 failure path: ${label} shows the error state and does not hang`, async ({ page }) => {
      const adapterErrors: string[] = [];
      page.on('console', (message) => {
        if (message.type() === 'error' && message.text().includes('[ResourceAdapter]')) {
          adapterErrors.push(message.text());
        }
      });
      await page.route('**/api/v1/customers/**', (route) =>
        fulfil === 'abort'
          ? route.abort('connectionrefused')
          : route.fulfill({ status: 500, contentType: 'application/json', body: '{}' }),
      );

      await page.goto('/customers');

      // The generated artifacts show no error state: the generated ResourceAdapter only
      // logs the failure. The alert is the host glue's own (tests/e2e/fixtures).
      await expect(page.getByTestId('customers-error')).toBeVisible();
      await expect(page.getByRole('alert')).toHaveText(/could not be loaded/);
      await expect(customerNames(page)).toHaveCount(0);
      await expect.poll(() => adapterErrors.length).toBeGreaterThan(0);
      expect(adapterErrors[0]).toContain('customers list failed');
      await page.screenshot({ path: screenshotPath(`P4-${fulfil}`) });
    });
  }
});
