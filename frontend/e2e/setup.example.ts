import { test as base, Page } from '@playwright/test';

/**
 * 测试夹具扩展
 * 提供全局的测试前置条件
 */

// 定义测试夹具类型
export interface MyFixtures {
  authenticatedPage: Page;
  apiURL: string;
}

// 扩展测试夹具
export const test = base.extend<MyFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // 在每个使用 authenticatedPage 的测试前执行登录
    // 注意：如果你的系统不需要认证，可以移除这部分

    // 示例：登录流程
    /*
    await page.goto('/login');
    await page.fill('input[name="username"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test@123456');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');
    */

    await use(page);
  },

  apiURL: async ({}, use) => {
    // 从环境变量或配置中获取 API 地址
    const apiURL = process.env.API_URL || 'http://localhost:8000/api/v1';
    await use(apiURL);
  }
});

export { expect } from '@playwright/test';
