# 测试用例使用示例

## 示例 1: 测试产品创建流程

```typescript
import { test, expect } from '@playwright/test';
import { createTestProduct, TestDataGenerator, waitForLoading } from '../helpers';

test('完整的产品创建流程', async ({ page }) => {
  // 生成测试数据
  const productData = {
    name: TestDataGenerator.productName(),
    vendor: '测试安全厂商',
    type: 'asset_mapping',
    description: '这是一个自动化测试创建的产品'
  };

  // 创建产品
  await page.goto('/products/create');
  await page.fill('input[placeholder*="产品名称"]', productData.name);
  await page.fill('input[placeholder*="厂商"]', productData.vendor);

  // 选择产品类型
  await page.click('.product-form .el-select');
  await page.click(`.el-select-dropdown__item:has-text("${productData.type}")`);

  // 填写描述
  await page.fill('textarea[placeholder*="描述"]', productData.description);

  // 提交
  await page.click('button:has-text("提交")');

  // 等待并验证
  await waitForLoading(page);

  // 应该导航到产品详情页
  expect(page.url()).toMatch(/\/products\/[a-f0-9-]+/);

  // 验证产品名称显示
  await expect(page.locator('text=' + productData.name)).toBeVisible();
});
```

## 示例 2: 测试文件上传

```typescript
import { test, expect } from '@playwright/test';
import { uploadFile, waitForMessage } from '../helpers';
import { join } from 'path';

test('从 Excel 文件创建需求', async ({ page }) => {
  await page.goto('/requirements/create');

  // 切换到文件上传
  await page.click('text=文件上传');

  // 准备测试文件路径
  const testFilePath = join(__dirname, '../test-data/sample-requirements.xlsx');

  // 上传文件
  await uploadFile(page, 'input[type="file"]', testFilePath);

  // 填写标题
  await page.fill('input[placeholder*="标题"]', 'Excel 需求测试');

  // 提交
  await page.click('button:has-text("提交")');

  // 等待成功消息
  await waitForMessage(page, 'success');

  // 验证创建成功
  await expect(page.locator('.el-message--success')).toBeVisible();
});
```

## 示例 3: 测试匹配分析完整流程

```typescript
import { test, expect } from '@playwright/test';
import { createTestRequirement, selectOption, waitForAPIResponse } from '../helpers';

test('需求到匹配的完整流程', async ({ page }) => {
  // 1. 创建测试需求
  await page.goto('/requirements/create');
  await page.fill('input[placeholder*="标题"]', '防火墙需求测试');
  await page.fill('textarea', '需要支持防火墙功能，包括访问控制、入侵检测等。');
  await page.click('button:has-text("提交")');

  // 等待创建完成
  await waitForLoading(page);

  // 2. 导航到匹配分析页面
  await page.goto('/matching');

  // 3. 选择需求
  await selectOption(page, '.requirement-selector', '防火墙需求测试');

  // 4. 配置匹配参数
  await page.fill('input[placeholder*="阈值"]', '0.8');

  // 5. 执行匹配（等待 API 响应）
  const matchButton = page.locator('button:has-text("开始匹配")');

  // 等待匹配 API 调用完成
  const [response] = await Promise.all([
    page.waitForResponse(r => r.url().includes('/matching/analyze')),
    matchButton.click()
  ]);

  // 验证 API 响应成功
  expect(response.status()).toBe(200);

  // 6. 验证匹配结果显示
  await expect(page.locator('.matching-results')).toBeVisible();

  // 7. 验证有匹配结果
  const resultRows = page.locator('.el-table__row');
  const count = await resultRows.count();
  expect(count).toBeGreaterThan(0);

  // 8. 查看第一个产品详情
  await resultRows.first().click();
  await expect(page.locator('.el-dialog')).toBeVisible();

  // 9. 关闭对话框
  await page.click('.el-dialog .el-dialog__headerbtn');
});
```

## 示例 4: 测试导出功能

```typescript
import { test, expect } from '@playwright/test';
import { Download } from '@playwright/test';

test('导出匹配结果报告', async ({ page }) => {
  // 先执行匹配分析...
  await page.goto('/matching');

  // 选择需求并执行匹配（简化代码）
  await page.click('.requirement-selector');
  await page.click('.el-select-dropdown__item:first-child');
  await page.click('button:has-text("开始匹配")');

  // 等待匹配完成
  await page.waitForTimeout(5000);

  // 点击导出按钮
  const downloadPromise = page.waitForEvent('download');
  await page.click('button:has-text("导出报告")');

  // 选择 Excel 格式
  await page.click('.el-dialog text=Excel');
  await page.click('.el-dialog button:has-text("确定")');

  // 等待下载完成
  const download: Download = await downloadPromise;

  // 验证下载文件
  expect(download.suggestedFilename()).toMatch(/\.(xlsx|xls)$/);
});
```

## 示例 5: 测试搜索和筛选

```typescript
import { test, expect } from '@playwright/test';

test('产品列表搜索和筛选', async ({ page }) => {
  await page.goto('/products');

  // 获取初始产品数量
  const initialCount = await page.locator('.el-table__row').count();

  // 测试搜索功能
  await page.fill('input[placeholder*="搜索"]', '防火墙');
  await page.waitForTimeout(500); // 等待搜索结果

  // 验证搜索结果
  const searchResults = page.locator('.el-table__row');
  const searchCount = await searchResults.count();

  // 搜索结果数量应该 <= 初始数量
  expect(searchCount).toBeLessThanOrEqual(initialCount);

  // 测试筛选功能
  await page.click('.filter-container .el-select');
  await page.click('.el-select-dropdown__item:has-text("asset_mapping")');

  // 等待筛选结果
  await page.waitForTimeout(500);

  // 验证筛选结果
  const filterResults = page.locator('.el-table__row');
  const filterCount = await filterResults.count();

  expect(filterCount).toBeGreaterThanOrEqual(0);

  // 清除筛选
  await page.click('.filter-clear, button:has-text("清除")');

  // 验证恢复到初始数量
  const finalCount = await page.locator('.el-table__row').count();
  expect(finalCount).toBe(initialCount);
});
```

## 示例 6: 测试表单验证

```typescript
import { test, expect } from '@playwright/test';

test('产品创建表单验证', async ({ page }) => {
  await page.goto('/products/create');

  // 测试 1: 验证必填字段
  await page.click('button:has-text("提交")');

  // 应该显示错误提示
  const errorMessages = page.locator('.el-form-item__error');
  await expect(errorMessages.first()).toBeVisible();

  // 测试 2: 验证产品名称长度
  await page.fill('input[placeholder*="产品名称"]', 'AB'); // 太短

  const nameError = page.locator('.product-name-field .el-form-item__error');
  if (await nameError.count() > 0) {
    await expect(nameError).toContainText('至少');
  }

  // 测试 3: 填写有效数据后错误消失
  await page.fill('input[placeholder*="产品名称"]', '有效产品名称ABC');

  // 错误应该消失
  await expect(nameError).not.toBeVisible();
});
```

## 示例 7: 测试响应式布局

```typescript
import { test, expect } from '@playwright/test';

test.describe('响应式设计测试', () => {
  test('桌面端布局', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/dashboard');

    // 桌面端应该显示侧边栏
    await expect(page.locator('.sidebar')).toBeVisible();

    // 统计卡片应该横向排列
    const statCards = page.locator('.stat-card');
    const firstCard = statCards.first();
    const secondCard = statCards.nth(1);

    const firstBox = await firstCard.boundingBox();
    const secondBox = await secondCard.boundingBox();

    expect(firstBox && secondBox && secondBox.x > firstBox.x).toBeTruthy();
  });

  test('移动端布局', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // 移动端侧边栏应该隐藏
    await expect(page.locator('.sidebar')).not.toBeVisible();

    // 应该显示菜单按钮
    await expect(page.locator('.menu-toggle')).toBeVisible();

    // 统计卡片应该纵向排列
    const statCards = page.locator('.stat-card');
    const firstCard = statCards.first();
    const secondCard = statCards.nth(1);

    const firstBox = await firstCard.boundingBox();
    const secondBox = await secondCard.boundingBox();

    expect(firstBox && secondBox && secondBox.y > firstBox.y).toBeTruthy();
  });
});
```

## 示例 8: 测试 API 错误处理

```typescript
import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';

test('处理 API 错误', async ({ page, context }) => {
  // 模拟 API 错误
  await context.route('**/api/v1/products/', route => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal Server Error' })
    });
  });

  await page.goto('/products');

  // 应该显示错误提示
  await expect(page.locator('.el-message--error')).toBeVisible();

  // 或者显示占位内容
  const emptyState = page.locator('.empty-state, .error-placeholder');
  if (await emptyState.count() > 0) {
    await expect(emptyState).toBeVisible();
  }
});
```

## 示例 9: 参数化测试

```typescript
import { test, expect } from '@playwright/test';

const testCases = [
  { name: '完全匹配', threshold: 0.9, expectedMin: 0.85 },
  { name: '中等匹配', threshold: 0.75, expectedMin: 0.75 },
  { name: '低匹配', threshold: 0.6, expectedMin: 0.6 }
];

for (const testCase of testCases) {
  test(`匹配阈值测试: ${testCase.name}`, async ({ page }) => {
    await page.goto('/matching');

    // 选择需求
    await page.click('.requirement-selector');
    await page.click('.el-select-dropdown__item:first-child');

    // 设置阈值
    await page.fill('input[placeholder*="阈值"]', testCase.threshold.toString());

    // 执行匹配
    await page.click('button:has-text("开始匹配")');
    await page.waitForTimeout(5000);

    // 验证结果符合阈值要求
    const scores = page.locator('.score-column, .similarity-value');
    const count = await scores.count();

    for (let i = 0; i < count; i++) {
      const scoreText = await scores.nth(i).textContent();
      const score = parseFloat(scoreText || '0');
      expect(score).toBeGreaterThanOrEqual(testCase.expectedMin);
    }
  });
}
```

## 示例 10: 使用页面对象模式

```typescript
// e2e/pages/ProductListPage.ts
import { Page, Locator } from '@playwright/test';

export class ProductListPage {
  readonly page: Page;
  readonly table: Locator;
  readonly searchInput: Locator;
  readonly createButton: Locator;
  readonly filterSelect: Locator;

  constructor(page: Page) {
    this.page = page;
    this.table = page.locator('.el-table');
    this.searchInput = page.locator('input[placeholder*="搜索"]');
    this.createButton = page.locator('button:has-text("创建产品")');
    this.filterSelect = page.locator('.filter-container .el-select');
  }

  async goto() {
    await this.page.goto('/products');
  }

  async search(keyword: string) {
    await this.searchInput.fill(keyword);
    await this.page.waitForTimeout(500);
  }

  async clickCreate() {
    await this.createButton.click();
  }

  async getRowCount() {
    return await this.page.locator('.el-table__row').count();
  }

  async filterByType(type: string) {
    await this.filterSelect.click();
    await this.page.locator(`.el-select-dropdown__item:has-text("${type}")`).click();
    await this.page.waitForTimeout(500);
  }
}

// 使用页面对象
import { test, expect } from '@playwright/test';
import { ProductListPage } from '../pages/ProductListPage';

test('使用页面对象测试产品列表', async ({ page }) => {
  const productListPage = new ProductListPage(page);

  await productListPage.goto();
  await productListPage.search('防火墙');

  const count = await productListPage.getRowCount();
  expect(count).toBeGreaterThan(0);
});
```

## 调试技巧

### 1. 暂停执行
```typescript
test('调试测试', async ({ page }) => {
  await page.goto('/products');
  await page.pause(); // 暂停并打开调试器
});
```

### 2. 截图
```typescript
test('失败时截图', async ({ page }) => {
  await page.goto('/products');

  try {
    // 测试代码
    await expect(page.locator('.product-list')).toBeVisible();
  } catch (error) {
    await page.screenshot({ path: 'failure-screenshot.png' });
    throw error;
  }
});
```

### 3. 控制台日志
```typescript
test('查看控制台日志', async ({ page }) => {
  page.on('console', msg => {
    console.log('浏览器日志:', msg.text());
  });

  await page.goto('/products');
});
```

### 4. 网络请求监听
```typescript
test('监听 API 请求', async ({ page }) => {
  page.on('request', request => {
    console.log('请求:', request.url());
  });

  page.on('response', response => {
    if (response.status() >= 400) {
      console.error('错误响应:', response.url(), response.status());
    }
  });

  await page.goto('/products');
});
```

## 最佳实践总结

1. ✅ 使用 `data-testid` 属性作为选择器（更稳定）
2. ✅ 等待元素可操作后再点击
3. ✅ 使用辅助函数避免代码重复
4. ✅ 测试失败时截图
5. ✅ 使用页面对象模式组织复杂页面
6. ✅ 参数化测试减少代码重复
7. ✅ 每个测试独立运行（不依赖其他测试）
8. ✅ 使用描述性的测试名称
9. ✅ 合理使用等待（避免硬编码 `setTimeout`）
10. ✅ Mock API 响应测试边界情况
