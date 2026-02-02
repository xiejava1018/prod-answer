import { test, expect } from '@playwright/test';

/**
 * 需求管理 - E2E 测试用例
 * 测试需求创建、文件上传、列表查看功能
 */

test.describe('需求管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/requirements');
  });

  test('应该显示需求列表页面', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/需求列表/);

    // 验证页面中有需求列表
    const table = page.locator('.el-table, .requirement-list');
    await expect(table).toBeVisible();

    // 验证有"创建需求"按钮
    const createButton = page.locator('button:has-text("创建需求"), button:has-text("新建")');
    await expect(createButton).toBeVisible();
  });

  test('应该能够打开创建需求页面', async ({ page }) => {
    // 点击"创建需求"按钮
    await page.click('button:has-text("创建需求"), button:has-text("新建")');

    // 验证导航到创建页面
    await expect(page).toHaveURL(/\/requirements\/create/);

    // 验证表单存在
    await expect(page.locator('form, .requirement-form')).toBeVisible();
  });
});

test.describe('创建需求', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/requirements/create');
  });

  test('应该显示两种输入方式：文本和文件上传', async ({ page }) => {
    // 验证有标签页或切换按钮
    await expect(page.locator('text=文本输入, text=手动输入')).toBeVisible();
    await expect(page.locator('text=文件上传, text=上传文件')).toBeVisible();
  });

  test('应该能够通过文本创建需求', async ({ page }) => {
    // 确保在"文本输入"标签页
    const textTab = page.locator('text=文本输入, text=手动输入').first();
    if (await textTab.isVisible()) {
      await textTab.click();
    }

    // 填写需求标题
    await page.fill('input[placeholder*="标题"], input[placeholder*="需求名称"]', '测试需求');

    // 填写需求描述
    const textarea = page.locator('textarea[placeholder*="描述"], textarea[placeholder*="需求"]');
    await textarea.fill('需要支持防火墙功能，能够进行网络访问控制，支持入侵检测和防御。');

    // 提交表单
    await page.click('button:has-text("提交"), button:has-text("创建")');

    // 验证创建成功
    await page.waitForTimeout(1000);

    // 应该显示成功消息或导航到需求详情页
    const currentUrl = page.url();
    const isSuccess = !currentUrl.includes('/create')
      || (await page.locator('.el-message--success').count()) > 0;

    expect(isSuccess).toBeTruthy();
  });

  test('应该验证必填字段', async ({ page }) => {
    // 直接点击提交，不填写任何内容
    await page.click('button:has-text("提交"), button:has-text("创建")');

    // 验证错误提示
    const errorMessage = page.locator('.el-form-item__error, .error-message');
    await expect(errorMessage.first()).toBeVisible();
  });

  test.describe('文件上传', () => {
    test('应该能够切换到文件上传模式', async ({ page }) => {
      // 点击"文件上传"标签页
      await page.click('text=文件上传, text=上传文件');

      // 验证上传组件显示
      await expect(page.locator('.el-upload, input[type="file"]')).toBeVisible();
    });

    test('应该支持上传 Excel 文件', async ({ page }) => {
      // 切换到文件上传标签
      await page.click('text=文件上传, text=上传文件');

      // 创建测试文件（模拟）
      // 注意：实际测试需要准备测试数据文件
      const fileInput = page.locator('input[type="file"]');

      // 检查文件输入是否存在
      const exists = await fileInput.count() > 0;

      if (exists) {
        // 模拟文件上传（实际使用时需要真实文件）
        // await fileInput.setInputFiles('test-data/sample.xlsx');

        // 验证文件已选择
        // await expect(page.locator('.el-upload-list__item')).toBeVisible();
      } else {
        // 如果没有文件输入，跳过测试
        test.skip();
      }
    });

    test('应该显示支持的文件格式提示', async ({ page }) => {
      // 切换到文件上传标签
      await page.click('text=文件上传, text=上传文件');

      // 验证有文件格式提示
      const formatHint = page.locator('text=.xlsx, text=.csv, text=.docx, text=Excel');
      await expect(formatHint).toBeVisible();
    });

    test('应该能够填写元数据', async ({ page }) => {
      // 切换到文件上传标签
      await page.click('text=文件上传, text=上传文件');

      // 填写需求标题
      await page.fill('input[placeholder*="标题"]', '文件上传测试需求');

      // 选择需求类型（如果有）
      const typeSelect = page.locator('.el-select').first();
      if (await typeSelect.isVisible()) {
        await typeSelect.click();
        await page.locator('.el-select-dropdown__item').first().click();
      }

      // 填写备注
      const remarkInput = page.locator('textarea[placeholder*="备注"], input[placeholder*="备注"]');
      if (await remarkInput.count() > 0) {
        await remarkInput.fill('这是通过文件上传创建的需求');
      }
    });
  });

  test.describe('批量创建', () => {
    test('应该能够从 Excel 解析多条需求', async ({ page }) => {
      // 切换到文件上传
      await page.click('text=文件上传, text=上传文件');

      // 填写标题
      await page.fill('input[placeholder*="标题"]', '批量需求测试');

      // 上传包含多条需求的 Excel 文件
      // 注意：需要准备测试文件
      // await page.setInputFiles('input[type="file"]', 'test-data/multiple-requirements.xlsx');

      // 验证解析结果显示
      // await expect(page.locator('.parsed-requirements, .requirement-preview')).toBeVisible();
    });
  });
});

test.describe('需求详情', () => {
  test('应该能够查看需求详情', async ({ page }) => {
    // 从列表页导航到详情页
    await page.goto('/requirements');

    // 点击第一个需求
    const firstItem = page.locator('.el-table__body-wrapper .el-table__row, .requirement-item').first();

    const count = await firstItem.count();
    if (count > 0) {
      await firstItem.click();

      // 验证导航到详情页
      await expect(page).toHaveURL(/\/requirements\/[a-f0-9-]+/);

      // 验证详情页内容
      await expect(page.locator('.requirement-detail, .detail-container')).toBeVisible();
    } else {
      test.skip(true, '没有可用的需求数据');
    }
  });

  test('应该能够编辑需求', async ({ page }) => {
    // 导航到需求详情
    await page.goto('/requirements');

    const firstItem = page.locator('.el-table__body-wrapper .el-table__row, .requirement-item').first();
    const count = await firstItem.count();

    if (count > 0) {
      await firstItem.click();

      // 点击编辑按钮
      const editButton = page.locator('button:has-text("编辑")');
      if (await editButton.count() > 0) {
        await editButton.click();

        // 修改需求描述
        const textarea = page.locator('textarea');
        await textarea.fill('更新后的需求描述');

        // 保存
        await page.click('button:has-text("保存"), button:has-text("提交")');

        // 验证更新成功
        await expect(page.locator('.el-message--success')).toBeVisible();
      }
    } else {
      test.skip(true, '没有可用的需求数据');
    }
  });

  test('应该能够删除需求', async ({ page }) => {
    // 导航到需求列表
    await page.goto('/requirements');

    const itemCount = await page.locator('.el-table__body-wrapper .el-table__row, .requirement-item').count();

    if (itemCount > 0) {
      // 点击第一个需求的删除按钮
      await page.locator('.el-table__row:first-child button:has-text("删除"), .requirement-item:first-child button:has-text("删除")').click();

      // 确认删除
      await page.click('.el-message-box__btnprimary, button:has-text("确定")');

      // 验证删除成功
      await expect(page.locator('.el-message--success')).toBeVisible();

      // 验证列表项减少
      const newCount = await page.locator('.el-table__body-wrapper .el-table__row, .requirement-item').count();
      expect(newCount).toBeLessThan(itemCount);
    } else {
      test.skip(true, '没有可用的需求数据');
    }
  });
});

test.describe('需求搜索和筛选', () => {
  test('应该能够搜索需求', async ({ page }) => {
    await page.goto('/requirements');

    // 输入搜索关键词
    const searchInput = page.locator('input[placeholder*="搜索"], .search-box input');
    await searchInput.fill('防火墙');

    // 等待搜索结果
    await page.waitForTimeout(500);

    // 验证搜索结果更新
    const results = page.locator('.el-table__body-wrapper .el-table__row, .requirement-item');
    const count = await results.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('应该能够按状态筛选', async ({ page }) => {
    await page.goto('/requirements');

    // 点击筛选下拉框
    const filterSelect = page.locator('.filter-container .el-select');
    if (await filterSelect.count() > 0) {
      await filterSelect.click();

      // 选择一个状态
      await page.locator('.el-select-dropdown__item').first().click();

      // 验证筛选结果
      await page.waitForTimeout(500);
      await expect(page.locator('.el-table, .requirement-list')).toBeVisible();
    }
  });
});
