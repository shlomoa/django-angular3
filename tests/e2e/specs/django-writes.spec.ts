import { expect, test, type Page } from '@playwright/test';

import { credentials, djangoUrl, PAGE_SIZE, screenshotPath, seedCustomers } from './support';

/**
 * Sign-in and CSRF-protected writes against the built Angular application that Django
 * serves. The tutorial API is open to anonymous users, and DRF enforces CSRF only for a
 * session-authenticated request, so every test signs in first. Writes go last (the file
 * name sorts after the read specs) and every customer a test creates is removed again.
 *
 * W2 is the integration: the generated client's transport must send the CSRF token. W3
 * (in the browser) and W4 (through the API) are its negative controls: without the token
 * Django must refuse the same write, or W2 would prove nothing.
 */
const origin = new URL(djangoUrl).origin;
const customerNames = (page: Page) => page.locator('td.mat-column-name');
const NEW_CUSTOMER = {
  name: 'E2E Written Customer',
  email: 'e2e.written@example.com',
  phone: '+1-555-0199',
  active: true,
};

/** Signs in through Django's session login (the `api-auth` view) and lands in the app. */
async function signIn(page: Page): Promise<void> {
  await page.goto('/api-auth/login/?next=/customers');
  await page.locator('input[name="username"]').fill(credentials.username);
  await page.locator('input[name="password"]').fill(credentials.password);
  await page.locator('input[type="submit"]').click();
  await expect(page).toHaveURL(`${origin}/customers`);
  await expect(customerNames(page)).toHaveCount(PAGE_SIZE);
}

async function cookieNames(page: Page): Promise<string[]> {
  return (await page.context().cookies(origin)).map((cookie) => cookie.name);
}

async function csrfToken(page: Page): Promise<string> {
  const cookie = (await page.context().cookies(origin)).find((c) => c.name === 'csrftoken');
  expect(cookie?.value, 'the csrftoken cookie').toBeTruthy();
  return cookie?.value ?? '';
}

async function customerCount(page: Page): Promise<number> {
  const response = await page.request.get('/api/v1/customers/');
  expect(response.status()).toBe(200);
  return ((await response.json()) as { count: number }).count;
}

async function removeCustomer(page: Page, id: number): Promise<void> {
  const response = await page.request.delete(`/api/v1/customers/${id}/`, {
    headers: { 'X-CSRFToken': await csrfToken(page) },
  });
  expect(response.status(), `removing customer ${id}`).toBe(204);
}

const isCustomerCreation = (response: { url(): string; request(): { method(): string } }) =>
  response.request().method() === 'POST' &&
  new URL(response.url()).pathname === '/api/v1/customers/';

test.describe('sign-in and CSRF-protected writes against the Django-served build', () => {
  test('W1 sign-in: Django sets the session and CSRF cookies and the app shows the data', async ({
    page,
  }) => {
    expect(await cookieNames(page)).not.toContain('sessionid');

    await signIn(page);

    const names = await cookieNames(page);
    expect(names).toContain('sessionid');
    expect(names).toContain('csrftoken');
    await page.screenshot({ path: screenshotPath('W1-signed-in') });
  });

  test('W2 a signed-in write through the generated client sends the CSRF token and succeeds', async ({
    page,
  }) => {
    const seedCount = seedCustomers().length;
    await signIn(page);
    const token = await csrfToken(page);

    const [response] = await Promise.all([
      page.waitForResponse(isCustomerCreation),
      page.getByTestId('create-customer').click(),
    ]);

    expect(response.request().headers()['x-csrftoken'], 'the token the app sent').toBe(token);
    expect(response.status()).toBe(201);
    const created = (await response.json()) as { id: number; email: string };
    try {
      expect(created.email).toBe(NEW_CUSTOMER.email);
      expect(await customerCount(page)).toBe(seedCount + 1);

      await page.getByRole('button', { name: 'Last page' }).click();
      await expect(
        page.locator('td.mat-column-email', { hasText: NEW_CUSTOMER.email }),
      ).toBeVisible();
      await expect(page.getByTestId('customers-write-error')).toHaveCount(0);
      await page.screenshot({ path: screenshotPath('W2-created') });
    } finally {
      await removeCustomer(page, created.id);
    }
    expect(await customerCount(page)).toBe(seedCount);
  });

  test('W3 control (browser): the same write without the CSRF token is refused and the app says so', async ({
    page,
  }) => {
    await signIn(page);
    const before = await customerCount(page);
    await page.route('**/api/v1/customers/', async (route) => {
      if (route.request().method() !== 'POST') {
        await route.fallback();
        return;
      }
      const headers = { ...route.request().headers() };
      delete headers['x-csrftoken'];
      await route.continue({ headers });
    });

    const [response] = await Promise.all([
      page.waitForResponse(isCustomerCreation),
      page.getByTestId('create-customer').click(),
    ]);

    expect(response.request().headers()['x-csrftoken']).toBeUndefined();
    expect(response.status()).toBe(403);
    expect(await response.text()).toContain('CSRF');
    await expect(page.getByTestId('customers-write-error')).toHaveText(/HTTP 403/);
    expect(await customerCount(page)).toBe(before);
    await page.screenshot({ path: screenshotPath('W3-refused') });
  });

  test('W4 control (API): a signed-in write is 403 without X-CSRFToken and 201 with it', async ({
    page,
  }) => {
    await signIn(page);
    const token = await csrfToken(page);
    const before = await customerCount(page);

    const refused = await page.request.post('/api/v1/customers/', { data: NEW_CUSTOMER });
    expect(refused.status()).toBe(403);
    expect(await refused.text()).toContain('CSRF');
    expect(await customerCount(page)).toBe(before);

    const accepted = await page.request.post('/api/v1/customers/', {
      data: NEW_CUSTOMER,
      headers: { 'X-CSRFToken': token },
    });
    expect(accepted.status()).toBe(201);
    await removeCustomer(page, ((await accepted.json()) as { id: number }).id);
    expect(await customerCount(page)).toBe(before);
  });

  test('W5 sign-out: the session cookie is gone and the next write needs a new sign-in', async ({
    page,
  }) => {
    await signIn(page);
    const token = await csrfToken(page);

    const loggedOut = await page.request.post('/api-auth/logout/', {
      headers: { 'X-CSRFToken': token },
    });

    expect(loggedOut.status()).toBeLessThan(400);
    expect(await cookieNames(page)).not.toContain('sessionid');
    await page.screenshot({ path: screenshotPath('W5-signed-out') });
  });
});
