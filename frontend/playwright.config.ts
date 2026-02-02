import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright 测试配置
 * 产品能力匹配系统 - E2E 测试
 */
export default defineConfig({
  testDir: './e2e',

  // 并行执行测试
  fullyParallel: true,

  // 在 CI 环境中失败时不重试
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,

  // 并发 worker 数量
  workers: process.env.CI ? 1 : undefined,

  // 测试报告
  reporter: [
    ['html'],
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],

  // 全局设置
  use: {
    // 基础 URL
    baseURL: process.env.BASE_URL || 'http://localhost:5173',

    // 追踪失败测试（用于调试）
    trace: 'off',  // 禁用追踪，避免需要额外依赖

    // 失败时截图
    screenshot: 'off',  // 禁用截图

    // 失败时录制视频
    video: 'off',  // 禁用视频录制

    // 浏览器视口大小
    viewport: { width: 1280, height: 720 },

    // 测试超时时间（毫秒）
    actionTimeout: 10000,
  },

  // 不同浏览器的测试项目
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // 开发服务器（可选）
  // 注意：如果你没有启动开发服务器，请注释掉这部分
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000,
  // },
});
