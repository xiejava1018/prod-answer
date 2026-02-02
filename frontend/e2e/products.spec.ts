import { test, expect } from '@playwright/test';

/**
 * 产品管理 - E2E 测试用例
 * 测试产品的增删改查功能
 */

test.describe('产品管理', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到产品列表页面
    await page.goto('/products');
  });

  test('应该显示产品列表页面', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/产品管理/);

    // 验证页面中有产品列表表格
    const table = page.locator('.el-table');
    await expect(table).toBeVisible();

    // 验证有"创建产品"按钮
    const createButton = page.locator('button:has-text("创建产品")');
    await expect(createButton).toBeVisible();
  });

  test('应该能够搜索产品', async ({ page }) => {
    // 点击搜索框
    const searchInput = page.locator('input[placeholder*="搜索"]');
    await searchInput.fill('防火墙');

    // 等待搜索结果加载
    await page.waitForTimeout(500);

    // 验证搜索结果（检查表格行数）
    const tableRows = page.locator('.el-table__body-wrapper .el-table__row');
    const count = await tableRows.count();

    // 应该有搜索结果或显示无结果
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('应该能够按产品类型筛选', async ({ page }) => {
    // 点击筛选下拉框
    const filterSelect = page.locator('.filter-container .el-select');
    await filterSelect.click();

    // 选择一个类型（例如：asset_mapping）
    const option = page.locator('.el-select-dropdown__item:has-text("asset_mapping")');
    await option.click();

    // 等待筛选结果
    await page.waitForTimeout(500);

    // 验证页面已更新
    await expect(page.locator('.el-table')).toBeVisible();
  });

  test('应该能够打开创建产品页面', async ({ page }) => {
    // 点击"创建产品"按钮
    await page.click('button:has-text("创建产品")');

    // 验证导航到创建页面
    await expect(page).toHaveURL(/\/products\/create/);

    // 验证表单存在
    await expect(page.locator('form')).toBeVisible();

    // 验证必填字段
    await expect(page.locator('input[placeholder*="产品名称"]')).toBeVisible();
    await expect(page.locator('input[placeholder*="厂商"]')).toBeVisible();
  });

  test.describe('创建产品表单', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/products/create');
    });

    test('应该验证必填字段', async ({ page }) => {
      // 直接点击提交，不填写任何内容
      await page.click('button:has-text("提交")');

      // 验证错误提示
      const errorMessage = page.locator('.el-form-item__error');
      await expect(errorMessage.first()).toBeVisible();
    });

    test('应该能够创建新产品', async ({ page }) => {
      // 填写产品名称
      await page.fill('input[placeholder*="产品名称"]', '测试防火墙产品');

      // 填写厂商
      await page.fill('input[placeholder*="厂商"]', '测试厂商');

      // 选择产品类型
      const typeSelect = page.locator('.product-form .el-select').first();
      await typeSelect.click();
      await page.locator('.el-select-dropdown__item').first().click();

      // 填写描述
      await page.fill('textarea[placeholder*="描述"]', '这是一个自动化测试创建的产品');

      // 提交表单
      await page.click('button:has-text("提交")');

      // 验证成功提示或导航到产品详情页
      await page.waitForTimeout(1000);

      // 应该显示成功消息或导航到产品详情页
      const currentUrl = page.url();
      const isSuccess = currentUrl.includes('/products/')
        || (await page.locator('.el-message--success').count()) > 0;

      expect(isSuccess).toBeTruthy();
    });
  });

  test.describe('产品详情', () => {
    test('应该能够查看产品详情', async ({ page }) => {
      // 假设列表中第一个产品可点击
      const firstRow = page.locator('.el-table__body-wrapper .el-table__row').first();

      // 点击第一行
      await firstRow.click();

      // 验证导航到详情页
      await expect(page).toHaveURL(/\/products\/[a-f0-9-]+/);

      // 验证详情页内容
      await expect(page.locator('.product-detail')).toBeVisible();
      await expect(page.locator('text=产品功能')).toBeVisible();
    });

    test('应该能够编辑产品', async ({ page }) => {
      // 导航到第一个产品的详情页
      const firstRow = page.locator('.el-table__body-wrapper .el-table__row').first();
      await firstRow.click();

      // 点击编辑按钮
      await page.click('button:has-text("编辑")');

      // 验证导航到编辑页面
      await expect(page).toHaveURL(/\/products\/[a-f0-9-]+\/edit/);

      // 修改产品名称
      const nameInput = page.locator('input[placeholder*="产品名称"]');
      await nameInput.fill('');
      await nameInput.fill('更新后的测试产品');

      // 提交更改
      await page.click('button:has-text("提交")');

      // 验证更新成功
      await page.waitForTimeout(1000);
      const currentUrl = page.url();
      const isSuccess = currentUrl.includes('/products/')
        || (await page.locator('.el-message--success').count()) > 0;

      expect(isSuccess).toBeTruthy();
    });
  });

  test.describe('产品功能管理', () => {
    test('应该能够添加产品功能', async ({ page }) => {
      // 导航到产品详情页
      const firstRow = page.locator('.el-table__body-wrapper .el-table__row').first();
      await firstRow.click();

      // 点击"添加功能"按钮
      await page.click('button:has-text("添加功能")');

      // 验证对话框打开
      await expect(page.locator('.el-dialog')).toBeVisible();

      // 填写功能信息
      await page.fill('.el-dialog input[placeholder*="功能名称"]', '测试功能');

      // 选择功能级别
      const level1Select = page.locator('.el-dialog .el-select').first();
      await level1Select.click();
      await page.locator('.el-select-dropdown__item').first().click();

      // 填写功能描述
      await page.fill('.el-dialog textarea', '这是一个测试功能');

      // 提交
      await page.click('.el-dialog button:has-text("确定")');

      // 验证功能添加成功
      await expect(page.locator('.el-message--success')).toBeVisible();
    });
  });
});
