# E2E 测试文档

## 概述

这是产品能力匹配系统的端到端（E2E）自动化测试套件，使用 [Playwright](https://playwright.dev/) 编写。

## 测试覆盖

### 1. 仪表盘测试 (`dashboard.spec.ts`)
- ✅ 页面加载验证
- ✅ 统计数据显示（产品、需求、匹配分析数量）
- ✅ 快速操作入口（创建产品、创建需求、开始匹配）
- ✅ 最近活动记录
- ✅ 数据可视化图表
- ✅ 响应式设计（移动端、平板）

### 2. 产品管理测试 (`products.spec.ts`)
- ✅ 产品列表显示
- ✅ 产品搜索和筛选
- ✅ 创建产品（表单验证、提交）
- ✅ 产品详情查看
- ✅ 编辑产品
- ✅ 产品功能管理（添加功能）

### 3. 需求管理测试 (`requirements.spec.ts`)
- ✅ 需求列表显示
- ✅ 通过文本创建需求
- ✅ 文件上传（Excel、CSV、Word）
- ✅ 文件解析和多条需求创建
- ✅ 需求详情查看
- ✅ 编辑和删除需求
- ✅ 需求搜索和筛选

### 4. 匹配分析测试 (`matching.spec.ts`)
- ✅ 匹配分析页面显示
- ✅ 选择需求进行匹配
- ✅ 配置匹配参数（阈值、产品类型）
- ✅ 执行匹配分析
- ✅ 匹配结果显示（完全匹配、部分匹配、未匹配）
- ✅ 匹配结果排序和筛选
- ✅ 导出匹配结果报告
- ✅ 匹配详情查看
- ✅ 功能级别的匹配详情
- ✅ 匹配性能测试

## 环境要求

- Node.js >= 18
- npm 或 yarn

## 安装

```bash
cd frontend

# 安装 Playwright
npm install -D @playwright/test

# 安装浏览器
npx playwright install
```

## 运行测试

### 运行所有测试
```bash
npx playwright test
```

### 运行特定测试文件
```bash
npx playwright test e2e/products.spec.ts
```

### 运行特定测试用例
```bash
npx playwright test -g "应该显示产品列表页面"
```

### 调试模式（带界面）
```bash
npx playwright test --ui
```

### 显示浏览器运行
```bash
npx playwright test --headed
```

### 查看测试报告
```bash
npx playwright show-report
```

## 配置

测试配置位于 `playwright.config.ts`：

- **基础 URL**: 默认 `http://localhost:5173`
- **浏览器**: Chromium、Firefox、WebKit
- **并发**: 默认并行运行
- **超时**: 单个测试 30 秒
- **重试**: CI 环境下失败重试 2 次

### 环境变量

可以通过环境变量覆盖配置：

```bash
# 设置不同的基础 URL
BASE_URL=http://localhost:8000 npx playwright test

# 设置并发数
WORKERS=1 npx playwright test
```

## 测试辅助函数

辅助函数位于 `e2e/helpers.ts`：

- `login()` - 用户登录
- `waitForLoading()` - 等待加载完成
- `waitForMessage()` - 等待消息提示
- `getTableData()` - 获取表格数据
- `selectOption()` - 选择下拉选项
- `uploadFile()` - 上传文件
- `confirmDialog()` - 确认对话框
- `createTestProduct()` - 创建测试产品
- `createTestRequirement()` - 创建测试需求
- `takeScreenshot()` - 截图
- `TestDataGenerator` - 测试数据生成器

## 测试数据准备

### 1. Excel 测试文件

创建 `test-data/requirements.xlsx`，格式：

| 标题         | 描述                               | 类型         |
|--------------|-----------------------------------|-------------|
| 防火墙需求    | 需要支持防火墙功能...              | 安全防护     |
| 日志分析需求  | 要求系统能够分析大量日志...        | 大数据分析   |

### 2. 测试账号

如果系统有认证功能，准备测试账号：

```
用户名: test@example.com
密码: Test@123456
```

## 最佳实践

### 1. 编写测试用例

```typescript
import { test, expect } from '@playwright/test';
import { createTestProduct, TestDataGenerator } from './helpers';

test('创建新产品', async ({ page }) => {
  const productData = {
    name: TestDataGenerator.productName(),
    vendor: '测试厂商',
    type: 'asset_mapping',
    description: '这是一个测试产品'
  };

  await createTestProduct(page, productData);

  // 验证结果
  await expect(page).toHaveURL(/\/products\/[a-f0-9-]+/);
});
```

### 2. 页面对象模式（推荐）

对于复杂页面，创建页面对象：

```typescript
// e2e/pages/ProductPage.ts
export class ProductPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/products');
  }

  async createProduct(data: ProductData) {
    await this.page.click('button:has-text("创建产品")');
    await this.page.fill('input[placeholder*="产品名称"]', data.name);
    // ...
  }

  async getProductCount() {
    return await this.page.locator('.el-table__row').count();
  }
}
```

### 3. 使用测试钩子

```typescript
test.describe('产品管理', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前执行
    await page.goto('/products');
  });

  test.afterEach(async ({ page }) => {
    // 每个测试后执行
    if (test.info().status !== 'passed') {
      await page.screenshot({ path: 'failure.png' });
    }
  });
});
```

## 调试技巧

### 1. 使用 VS Code 调试
安装 [Playwright Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright)

### 2. 慢动作模式
```bash
npx playwright test --headed --slow-mo=1000
```

### 3. 暂停执行
```typescript
test('调试测试', async ({ page }) => {
  await page.pause(); // 暂停并打开调试器
});
```

### 4. 查看截图和视频
测试失败后，查看 `test-results/` 目录：
- 截图: `test-results/screenshots/`
- 视频: `test-results/videos/`
- 追踪: `test-results/traces/`（使用 `npx playwright show-trace` 查看）

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Run tests
        run: |
          cd frontend
          npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## 常见问题

### 1. 测试超时
增加超时时间：
```typescript
test.setTimeout(60000); // 60秒
```

### 2. 元素未找到
使用等待：
```typescript
await page.waitForSelector('.my-element', { timeout: 10000 });
```

### 3. 测试不稳定
- 使用 `waitForLoading()` 等待加载完成
- 使用 `safeClick()` 代替直接点击
- 增加重试次数

### 4. 无头模式失败
使用 `--headed` 查看实际执行情况

## 贡献

添加新测试时：
1. 使用清晰的测试名称
2. 遵循现有测试结构
3. 添加适当的断言
4. 复用辅助函数
5. 更新文档

## 资源

- [Playwright 官方文档](https://playwright.dev/)
- [最佳实践指南](https://playwright.dev/docs/best-practices)
- [API 参考](https://playwright.dev/docs/api/class-playwright)
