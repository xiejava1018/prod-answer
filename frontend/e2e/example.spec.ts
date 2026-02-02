import { test, expect } from '@playwright/test';

/**
 * 简单的示例测试 - 验证 Playwright 配置
 * 这个测试不需要应用运行，只是验证测试框架工作正常
 */

test('基础测试 - 验证页面标题', async ({ page }) => {
  // 访问一个简单的网页（使用 example.com）
  await page.goto('https://example.com');

  // 验证页面标题
  await expect(page).toHaveTitle('Example Domain');

  // 验证页面内容
  const heading = page.locator('h1');
  await expect(heading).toContainText('Example Domain');
});

test('基础测试 - 验证页面导航', async ({ page }) => {
  // 访问 example.com
  await page.goto('https://example.com');

  // 验证当前 URL
  expect(page.url()).toBe('https://example.com/');

  // 获取页面标题
  const title = await page.title();
  expect(title).toBe('Example Domain');
});

test('基础测试 - 元素查找和交互', async ({ page }) => {
  await page.goto('https://example.com');

  // 查找 h1 元素
  const h1 = page.locator('h1');
  await expect(h1).toBeVisible();

  // 获取元素文本
  const text = await h1.textContent();
  expect(text).toBe('Example Domain');

  // 查找段落
  const paragraph = page.locator('p');
  await expect(paragraph).toBeVisible();
  const pText = await paragraph.textContent();
  expect(pText).toContain('This domain is for use in illustrative examples');
});

test('基础测试 - 截图功能', async ({ page }) => {
  await page.goto('https://example.com');

  // 截图保存到 test-results/screenshots
  await page.screenshot({
    path: 'test-results/screenshots/example.png',
    fullPage: true
  });

  // 验证截图文件存在（通过检查操作是否成功）
  // 如果截图失败，上面的方法会抛出错误
  expect(true).toBe(true);
});
