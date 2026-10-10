import { expect, test, type Page } from '@playwright/test';

import {
  collectErrors,
  djangoUrl,
  PAGE_SIZE,
  screenshotPath,
  seedCustomers,
} from './support';

/**
 * Django alone serves the built Angular application (`django_angular3.spa`): the pages, the
 * assets and the API share one origin, with no dev server, proxy or CORS configuration.
 */
const origin = new URL(djangoUrl).origin;
const customerNames = (page: Page) => page.locator('td.mat-column-name');

test.describe('the built Angular application served by Django', () => {
  for (const route of ['/customers', '/products']) {
    test(`D1 hard refresh on ${route} returns the application, not a Django 404`, async ({
      page,
    }) => {
      const errors = collectErrors(page);

      const response = await page.goto(route);

      expect(response?.status()).toBe(200);
      expect(response?.headers()['content-type']).toContain('text/html');
      await expect(page).toHaveURL(`${origin}${route}`);
      await expect(page.locator('mat-sidenav a[mat-list-item]')).toHaveText([
        /Home/,
        /Customers/,
        /Products/,
      ]);
      if (route === '/customers') {
        const seed = seedCustomers();
        await expect(customerNames(page)).toHaveCount(PAGE_SIZE);
        await expect(customerNames(page)).toHaveText(
          seed.slice(0, PAGE_SIZE).map((customer) => customer.name),
        );
      }
      await page.screenshot({ path: screenshotPath(`D1-refresh${route.replace('/', '-')}`) });

      expect(errors, 'console and page errors').toEqual([]);
    });
  }

  test('D2 in-app navigation is Angular routing: one document request, then the API only', async ({
    page,
  }) => {
    const documents: string[] = [];
    page.on('request', (request) => {
      if (request.isNavigationRequest()) {
        documents.push(new URL(request.url()).pathname);
      }
    });

    await page.goto('/');
    await page.locator('mat-sidenav a[mat-list-item]', { hasText: 'Customers' }).click();
    await expect(page).toHaveURL(`${origin}/customers`);
    await expect(customerNames(page)).toHaveCount(PAGE_SIZE);

    await page.locator('mat-sidenav a[mat-list-item]', { hasText: 'Products' }).click();
    await expect(page).toHaveURL(`${origin}/products`);

    expect(documents, 'document requests made while navigating').toEqual(['/']);
    await page.screenshot({ path: screenshotPath('D2-products') });
  });

  test('D3 the API stays Django: JSON for a route, a 404 (not index.html) for a wrong URL', async ({
    request,
  }) => {
    const list = await request.get('/api/v1/customers/?page=1');
    expect(list.status()).toBe(200);
    expect(list.headers()['content-type']).toContain('application/json');
    expect(((await list.json()) as { count: number }).count).toBe(seedCustomers().length);

    const wrong = await request.get('/api/v1/nope/');
    expect(wrong.status()).toBe(404);
    expect(await wrong.text()).not.toContain('<app-root');
  });

  test('D4 the admin stays Django', async ({ page }) => {
    const response = await page.goto('/admin/login/');

    expect(response?.status()).toBe(200);
    await expect(page).toHaveTitle(/Log in \| Django site admin/);
    await expect(page.locator('app-root')).toHaveCount(0);
    await page.screenshot({ path: screenshotPath('D4-admin') });
  });

  test('D5 one origin: every API call goes to Django and no CORS headers are involved', async ({
    page,
    request,
  }) => {
    const requested: string[] = [];
    page.on('request', (request) => requested.push(request.url()));

    await page.goto('/customers');
    await expect(customerNames(page)).toHaveCount(PAGE_SIZE);

    const api = requested.filter((url) => new URL(url).pathname.startsWith('/api/'));
    expect(api.length, 'API requests of the page').toBeGreaterThan(0);
    for (const url of api) {
      expect(new URL(url).origin).toBe(origin);
    }
    // Nothing is fetched from an Angular dev server; only web fonts may leave the origin.
    const foreign = requested
      .map((url) => new URL(url))
      .filter((url) => url.protocol.startsWith('http') && url.origin !== origin)
      .map((url) => url.hostname);
    for (const host of foreign) {
      expect(['fonts.googleapis.com', 'fonts.gstatic.com']).toContain(host);
    }

    // A cross-origin caller would need CORS; Django sends none because none is needed.
    const crossOrigin = await request.get('/api/v1/customers/', {
      headers: { Origin: 'http://localhost:4200' },
    });
    expect(crossOrigin.headers()['access-control-allow-origin']).toBeUndefined();
  });

  test('D6 the bundle is served by Django: scripts and styles load, a stale hash is a 404', async ({
    page,
    request,
  }) => {
    await page.goto('/customers');
    await expect(customerNames(page)).toHaveCount(PAGE_SIZE);

    const assets = await page.evaluate(() =>
      performance
        .getEntriesByType('resource')
        .map((entry) => entry.name)
        .filter((name) => /\.(js|css)$/.test(new URL(name).pathname)),
    );
    const local = assets.filter((name) => new URL(name).origin === origin);
    expect(local.some((name) => name.endsWith('.js')), 'a script of the bundle').toBe(true);
    expect(local.some((name) => name.endsWith('.css')), 'a stylesheet of the bundle').toBe(true);
    for (const name of local) {
      const response = await request.get(new URL(name).pathname);
      expect(response.status(), name).toBe(200);
      expect(response.headers()['content-type'], name).toMatch(/javascript|css/);
    }

    expect((await request.get('/main-DEADBEEF.js')).status()).toBe(404);
  });
});
