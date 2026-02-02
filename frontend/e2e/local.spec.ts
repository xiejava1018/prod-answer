import { test as base, chromium, expect } from '@playwright/test';

/**
 * 使用系统安装的 Chrome 浏览器进行测试
 * 这个测试不需要下载 Playwright 浏览器
 */

// 扩展 test 配置，使用系统 Chrome
export const test = base.extend({
  browser: async ({ }, use) => {
    // 使用系统安装的 Chrome
    const browser = await chromium.launch({
      executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      headless: false  // 显示浏览器窗口
    });
    await use(browser);
    await browser.close();
  }
});

test('示例测试 - 访问 Example.com', async ({ page, context }) => {
  // 访问 example.com
  await page.goto('https://example.com');

  // 验证页面标题
  const title = await page.title();
  console.log('页面标题:', title);

  // 验证 h1 标题
  const h1Text = await page.locator('h1').textContent();
  console.log('H1 内容:', h1Text);

  // 断言
  expect(title).toBe('Example Domain');
  expect(h1Text).toBe('Example Domain');
});
