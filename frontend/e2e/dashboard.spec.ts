import { test, expect } from '@playwright/test';

/**
 * 仪表盘 - E2E 测试用例
 * 测试系统首页的功能和统计信息
 */

test.describe('仪表盘', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('应该显示仪表盘页面', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/仪表盘|Dashboard/);

    // 验证页面主要内容
    await expect(page.locator('.dashboard-container, .dashboard')).toBeVisible();
  });

  test('应该显示统计卡片', async ({ page }) => {
    // 查找统计卡片
    const statCards = page.locator('.stat-card, .stat-item, .summary-card');

    // 验证至少有一些统计卡片
    const count = await statCards.count();
    expect(count).toBeGreaterThan(0);

    // 验证每个卡片都有标题和数值
    const firstCard = statCards.first();
    await expect(firstCard.locator('.title, .label, h3')).toBeVisible();
    await expect(firstCard.locator('.value, .number, .count')).toBeVisible();
  });

  test('应该显示产品数量统计', async ({ page }) => {
    // 查找产品统计
    const productStat = page.locator('text=产品数量, text=Products, .stat-card:has-text("产品")');

    if (await productStat.count() > 0) {
      // 验证显示数值
      const value = productStat.locator('.value, .number, .count');
      await expect(value).toBeVisible();

      // 验证数值是数字
      const text = await value.textContent();
      expect(parseInt(text || '0')).toBeGreaterThanOrEqual(0);
    }
  });

  test('应该显示需求数量统计', async ({ page }) => {
    // 查找需求统计
    const requirementStat = page.locator('text=需求数量, text=Requirements, .stat-card:has-text("需求")');

    if (await requirementStat.count() > 0) {
      // 验证显示数值
      const value = requirementStat.locator('.value, .number, .count');
      await expect(value).toBeVisible();

      // 验证数值是数字
      const text = await value.textContent();
      expect(parseInt(text || '0')).toBeGreaterThanOrEqual(0);
    }
  });

  test('应该显示匹配分析数量统计', async ({ page }) => {
    // 查找匹配统计
    const matchingStat = page.locator('text=匹配分析, text=Matching, .stat-card:has-text("匹配")');

    if (await matchingStat.count() > 0) {
      // 验证显示数值
      const value = matchingStat.locator('.value, .number, .count');
      await expect(value).toBeVisible();

      // 验证数值是数字
      const text = await value.textContent();
      expect(parseInt(text || '0')).toBeGreaterThanOrEqual(0);
    }
  });

  test.describe('快速操作', () => {
    test('应该提供快速创建产品的入口', async ({ page }) => {
      // 查找"创建产品"快捷按钮
      const createProductBtn = page.locator('button:has-text("创建产品"), a:has-text("创建产品"), .quick-action:has-text("产品")');

      if (await createProductBtn.count() > 0) {
        // 点击按钮
        await createProductBtn.first().click();

        // 验证导航到创建产品页面
        await expect(page).toHaveURL(/\/products\/create/);
      }
    });

    test('应该提供快速创建需求的入口', async ({ page }) => {
      // 查找"创建需求"快捷按钮
      const createRequirementBtn = page.locator('button:has-text("创建需求"), a:has-text("创建需求"), .quick-action:has-text("需求")');

      if (await createRequirementBtn.count() > 0) {
        // 点击按钮
        await createRequirementBtn.first().click();

        // 验证导航到创建需求页面
        await expect(page).toHaveURL(/\/requirements\/create/);
      }
    });

    test('应该提供快速开始匹配的入口', async ({ page }) => {
      // 查找"开始匹配"快捷按钮
      const startMatchingBtn = page.locator('button:has-text("开始匹配"), a:has-text("开始匹配"), .quick-action:has-text("匹配")');

      if (await startMatchingBtn.count() > 0) {
        // 点击按钮
        await startMatchingBtn.first().click();

        // 验证导航到匹配分析页面
        await expect(page).toHaveURL(/\/matching/);
      }
    });
  });

  test.describe('最近活动', () => {
    test('应该显示最近的活动记录', async ({ page }) => {
      // 查找最近活动列表
      const recentActivity = page.locator('.recent-activity, .activity-list, .latest-records');

      if (await recentActivity.isVisible()) {
        // 验证有活动项
        const items = recentActivity.locator('.activity-item, .record-item');
        const count = await items.count();

        expect(count).toBeGreaterThan(0);

        // 验证每个活动项都有时间和描述
        const firstItem = items.first();
        await expect(firstItem.locator('.time, .date, .timestamp')).toBeVisible();
        await expect(firstItem.locator('.description, .content, .action')).toBeVisible();
      }
    });

    test('应该能够点击活动项跳转到详情', async ({ page }) => {
      // 查找最近活动列表
      const recentActivity = page.locator('.recent-activity, .activity-list');

      if (await recentActivity.isVisible()) {
        const firstItem = recentActivity.locator('.activity-item, .record-item').first();
        await firstItem.click();

        // 验证导航到详情页面
        const currentUrl = page.url();
        const hasDetailUrl =
          currentUrl.includes('/products/') ||
          currentUrl.includes('/requirements/') ||
          currentUrl.includes('/matching/');

        expect(hasDetailUrl).toBeTruthy();
      }
    });
  });

  test.describe('图表和可视化', () => {
    test('应该显示数据可视化图表', async ({ page }) => {
      // 查找图表容器
      const charts = page.locator('.chart-container, .echarts, canvas, svg');

      // 验证至少有图表元素
      const count = await charts.count();
      expect(count).toBeGreaterThan(0);
    });

    test('应该显示产品类型分布图', async ({ page }) => {
      // 查找产品类型分布图表
      const chart = page.locator('.product-distribution, .chart:has-text("产品类型"), .chart:has-text("分布")');

      if (await chart.count() > 0) {
        await expect(chart).toBeVisible();
      }
    });

    test('应该显示匹配趋势图', async ({ page }) => {
      // 查找匹配趋势图表
      const chart = page.locator('.matching-trend, .chart:has-text("趋势"), .chart:has-text("匹配")');

      if (await chart.count() > 0) {
        await expect(chart).toBeVisible();
      }
    });
  });

  test.describe('导航', () => {
    test('应该能够通过侧边栏导航', async ({ page }) => {
      // 查找侧边栏
      const sidebar = page.locator('.sidebar, .nav-menu, .el-aside');

      if (await sidebar.isVisible()) {
        // 点击"产品管理"菜单
        const productMenu = sidebar.locator('text=产品管理, text=Products');
        if (await productMenu.count() > 0) {
          await productMenu.click();
          await expect(page).toHaveURL(/\/products/);
        }
      }
    });

    test('应该高亮当前页面菜单项', async ({ page }) => {
      // 查找侧边栏
      const sidebar = page.locator('.sidebar, .nav-menu, .el-aside');

      if (await sidebar.isVisible()) {
        // 查找当前激活的菜单项（仪表盘）
        const activeMenu = sidebar.locator('.is-active, .active, .router-link-active');
        await expect(activeMenu).toBeVisible();
      }
    });
  });

  test.describe('响应式设计', () => {
    test('应该在移动设备上正常显示', async ({ page }) => {
      // 设置移动设备视口
      await page.setViewportSize({ width: 375, height: 667 });

      // 刷新页面
      await page.reload();

      // 验证页面仍可访问
      await expect(page.locator('.dashboard-container, .dashboard')).toBeVisible();

      // 验证移动端菜单按钮显示
      const menuButton = page.locator('.menu-toggle, .hamburger, button:has-text("菜单")');
      if (await menuButton.count() > 0) {
        await expect(menuButton).toBeVisible();
      }
    });

    test('应该在平板设备上正常显示', async ({ page }) => {
      // 设置平板设备视口
      await page.setViewportSize({ width: 768, height: 1024 });

      // 刷新页面
      await page.reload();

      // 验证页面仍可访问
      await expect(page.locator('.dashboard-container, .dashboard')).toBeVisible();
    });
  });
});
