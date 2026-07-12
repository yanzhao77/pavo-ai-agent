import { test, expect } from '@playwright/test';

test('homepage loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('text=Pavo AI Agent')).toBeVisible();
});

test('auth login form appears', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('text=Enter your username')).toBeVisible();
});
