import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const browser = await chromium.launch({
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
});
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:3000');
  await page.getByRole('heading', { name: 'The Agent Foundry', exact: true }).waitFor();
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await mkdir('docs/images', { recursive: true });
  await page.screenshot({ path: 'docs/images/desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: 'docs/images/mobile.png', fullPage: true });
  console.log('Saved desktop and mobile demo screenshots in docs/images.');
} finally {
  await browser.close();
}
