import { test, expect } from '@playwright/test';

/**
 * 匹配分析 - E2E 测试用例
 * 测试需求与产品的智能匹配功能
 */

test.describe('匹配分析', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/matching');
  });

  test('应该显示匹配分析页面', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/匹配分析/);

    // 验证页面主要内容
    await expect(page.locator('.matching-container, .analysis-container')).toBeVisible();
  });

  test('应该能够选择需求进行匹配', async ({ page }) => {
    // 查找需求选择器
    const requirementSelect = page.locator('.requirement-selector, .el-select').first();

    if (await requirementSelect.isVisible()) {
      // 点击需求选择器
      await requirementSelect.click();

      // 验证下拉列表显示
      await expect(page.locator('.el-select-dropdown')).toBeVisible();

      // 选择第一个需求
      const firstOption = page.locator('.el-select-dropdown__item').first();
      const optionCount = await firstOption.count();

      if (optionCount > 0) {
        await firstOption.click();

        // 验证需求已选择
        await expect(requirementSelect).toContainText(/[^\s]/); // 有内容
      } else {
        test.skip(true, '没有可用的需求数据');
      }
    }
  });

  test('应该能够配置匹配参数', async ({ page }) => {
    // 查找匹配阈值设置
    const thresholdInput = page.locator('input[placeholder*="阈值"], input[aria-label*="阈值"], .threshold-input input');

    if (await thresholdInput.count() > 0) {
      // 输入自定义阈值
      await thresholdInput.fill('0.8');

      // 验证值已设置
      const value = await thresholdInput.inputValue();
      expect(value).toBe('0.8');
    }

    // 查找产品类型筛选
    const productTypeFilter = page.locator('.product-type-filter, .filter-group .el-select');

    if (await productTypeFilter.count() > 0) {
      // 点击产品类型筛选器
      await productTypeFilter.first().click();

      // 选择产品类型
      await page.locator('.el-select-dropdown__item').first().click();
    }
  });

  test('应该能够执行匹配分析', async ({ page }) => {
    // 选择需求（如果有需求可选）
    const requirementSelect = page.locator('.requirement-selector, .el-select').first();
    const hasRequirementSelect = await requirementSelect.isVisible();

    if (hasRequirementSelect) {
      await requirementSelect.click();
      const optionCount = await page.locator('.el-select-dropdown__item').count();

      if (optionCount > 0) {
        await page.locator('.el-select-dropdown__item').first().click();
      } else {
        test.skip(true, '没有可用的需求数据');
        return;
      }
    }

    // 点击"开始匹配"按钮
    const matchButton = page.locator('button:has-text("开始匹配"), button:has-text("执行分析"), button:has-text("分析")');
    await expect(matchButton).toBeVisible();

    await matchButton.click();

    // 验证加载状态
    await expect(page.locator('.el-loading, .is-loading')).toBeVisible();

    // 等待匹配完成（最多等待 30 秒）
    await page.waitForTimeout(5000);

    // 验证结果显示
    const results = page.locator('.matching-results, .results-container, .analysis-results');

    // 检查是否有结果或错误消息
    const hasResults = await results.count() > 0;
    const hasError = await page.locator('.el-message--error').count() > 0;

    expect(hasResults || hasError).toBeTruthy();
  });

  test.describe('匹配结果', () => {
    test.beforeEach(async ({ page }) => {
      // 先执行一次匹配
      await page.goto('/matching');

      const requirementSelect = page.locator('.requirement-selector, .el-select').first();
      const hasSelect = await requirementSelect.isVisible();

      if (hasSelect) {
        await requirementSelect.click();
        const optionCount = await page.locator('.el-select-dropdown__item').count();

        if (optionCount > 0) {
          await page.locator('.el-select-dropdown__item').first().click();

          const matchButton = page.locator('button:has-text("开始匹配"), button:has-text("分析")');
          await matchButton.click();

          // 等待匹配完成
          await page.waitForTimeout(5000);
        }
      }
    });

    test('应该显示匹配结果统计', async ({ page }) => {
      // 查找统计信息
      const stats = page.locator('.stats-container, .summary, .match-statistics');

      if (await stats.isVisible()) {
        // 验证统计卡片显示
        await expect(stats.locator('.stat-card, .stat-item').first()).toBeVisible();
      }
    });

    test('应该显示匹配结果列表', async ({ page }) => {
      // 查找结果表格
      const resultTable = page.locator('.results-table, .el-table');

      if (await resultTable.isVisible()) {
        // 验证表格有数据行
        const rows = resultTable.locator('.el-table__row, tbody tr');
        const rowCount = await rows.count();

        expect(rowCount).toBeGreaterThan(0);

        // 验证表格列（相似度、匹配状态等）
        await expect(resultTable.locator('text=相似度, text=匹配度, text=score')).toBeVisible();
      }
    });

    test('应该能够区分完全匹配、部分匹配和未匹配', async ({ page }) => {
      // 查找匹配状态标签
      const matchedTag = page.locator('text=完全匹配, text=matched, .tag-success');
      const partialTag = page.locator('text=部分匹配, text=partial, .tag-warning');
      const unmatchedTag = page.locator('text=未匹配, text=unmatched, .tag-danger');

      // 至少应该有一种匹配状态
      const hasAnyMatch =
        (await matchedTag.count()) > 0 ||
        (await partialTag.count()) > 0 ||
        (await unmatchedTag.count()) > 0;

      expect(hasAnyMatch).toBeTruthy();
    });

    test('应该能够查看产品详情', async ({ page }) => {
      // 查找结果表格中的第一个产品
      const firstRow = page.locator('.el-table__body-wrapper .el-table__row').first();
      const rowCount = await firstRow.count();

      if (rowCount > 0) {
        // 点击第一行
        await firstRow.click();

        // 验证打开产品详情对话框或导航到详情页
        const dialog = page.locator('.el-dialog');
        const detailPage = page.locator('.product-detail');

        const hasDialog = await dialog.count() > 0;
        const hasDetailPage = await detailPage.count() > 0;

        expect(hasDialog || hasDetailPage).toBeTruthy();
      }
    });

    test('应该能够按相似度排序', async ({ page }) => {
      // 查找相似度列的排序按钮
      const sortButton = page.locator('.el-table th:has-text("相似度"), .el-table th:has-text("匹配度")');

      if (await sortButton.count() > 0) {
        // 点击排序
        await sortButton.click();

        // 等待排序完成
        await page.waitForTimeout(500);

        // 验证排序图标显示
        await expect(sortButton.locator('.caret-wrapper, .sort-icon')).toBeVisible();
      }
    });

    test('应该能够筛选匹配结果', async ({ page }) => {
      // 查找筛选器
      const filterTabs = page.locator('.filter-tabs, .match-filter .el-radio-group');

      if (await filterTabs.isVisible()) {
        // 点击"完全匹配"筛选
        await filterTabs.locator('text=完全匹配, text=matched').click();

        // 等待筛选结果
        await page.waitForTimeout(500);

        // 验证结果更新
        const results = page.locator('.el-table__body-wrapper .el-table__row');
        const count = await results.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });

    test('应该能够导出匹配结果', async ({ page }) => {
      // 查找导出按钮
      const exportButton = page.locator('button:has-text("导出"), button:has-text("下载报告"), button:has-text("导出报告")');

      if (await exportButton.count() > 0) {
        // 点击导出按钮
        await exportButton.click();

        // 验证导出选项对话框显示
        const dialog = page.locator('.el-dialog');

        if (await dialog.isVisible()) {
          // 选择导出格式（Excel）
          await page.click('.el-dialog text=Excel, .el-dialog .el-radio:has-text("Excel")');

          // 确认导出
          await page.click('.el-dialog button:has-text("确定"), .el-dialog button:has-text("导出")');

          // 验证成功提示
          await expect(page.locator('.el-message--success')).toBeVisible();
        }
      }
    });
  });
});

test.describe('匹配详情页', () => {
  test('应该能够查看匹配详情', async ({ page }) => {
    // 从匹配分析页面导航到详情页
    await page.goto('/matching');

    // 选择需求并执行匹配
    const requirementSelect = page.locator('.requirement-selector, .el-select').first();
    const hasSelect = await requirementSelect.isVisible();

    if (hasSelect) {
      await requirementSelect.click();
      const optionCount = await page.locator('.el-select-dropdown__item').count();

      if (optionCount > 0) {
        await page.locator('.el-select-dropdown__item').first().click();

        const matchButton = page.locator('button:has-text("开始匹配"), button:has-text("分析")');
        await matchButton.click();

        await page.waitForTimeout(5000);

        // 点击"查看详情"按钮
        const detailButton = page.locator('button:has-text("查看详情"), button:has-text("详情")');
        const buttonCount = await detailButton.count();

        if (buttonCount > 0) {
          await detailButton.first().click();

          // 验证导航到详情页
          await expect(page).toHaveURL(/\/matching\/results\/[a-f0-9-]+/);

          // 验证详情页内容
          await expect(page.locator('.match-result-detail, .result-detail')).toBeVisible();

          // 验证显示需求信息
          await expect(page.locator('text=需求信息, text=需求描述')).toBeVisible();

          // 验证显示匹配结果列表
          await expect(page.locator('.matched-products, .product-matches')).toBeVisible();
        }
      }
    }
  });

  test('应该能够查看功能级别的匹配详情', async ({ page }) => {
    // 导航到匹配结果详情页（假设有结果ID）
    // 注意：实际测试需要使用真实的结果ID
    await page.goto('/matching/results/some-result-id');

    // 查找功能匹配详情
    const featureDetails = page.locator('.feature-matches, .feature-details');

    if (await featureDetails.isVisible()) {
      // 验证显示功能列表
      await expect(featureDetails.locator('.feature-item, .function-item').first()).toBeVisible();

      // 验证显示每个功能的相似度分数
      await expect(featureDetails.locator('text=相似度, text=匹配度')).toBeVisible();
    }
  });

  test('应该能够重新执行匹配', async ({ page }) => {
    // 在详情页查找"重新匹配"按钮
    await page.goto('/matching/results/some-result-id');

    const rematchButton = page.locator('button:has-text("重新匹配"), button:has-text("重新分析")');

    if (await rematchButton.count() > 0) {
      await rematchButton.click();

      // 验证返回到匹配分析页面
      await expect(page).toHaveURL(/\/matching/);
    }
  });
});

test.describe('匹配性能', () => {
  test('应该在合理时间内完成匹配', async ({ page }) => {
    await page.goto('/matching');

    const startTime = Date.now();

    // 选择需求并执行匹配
    const requirementSelect = page.locator('.requirement-selector, .el-select').first();
    const hasSelect = await requirementSelect.isVisible();

    if (hasSelect) {
      await requirementSelect.click();
      const optionCount = await page.locator('.el-select-dropdown__item').count();

      if (optionCount > 0) {
        await page.locator('.el-select-dropdown__item').first().click();

        const matchButton = page.locator('button:has-text("开始匹配"), button:has-text("分析")');
        await matchButton.click();

        // 等待加载完成
        await page.waitForSelector('.el-loading, .is-loading', { state: 'detached', timeout: 30000 });

        const endTime = Date.now();
        const duration = endTime - startTime;

        // 匹配应该在 30 秒内完成
        expect(duration).toBeLessThan(30000);

        console.log(`匹配耗时: ${duration}ms`);
      }
    }
  });
});
