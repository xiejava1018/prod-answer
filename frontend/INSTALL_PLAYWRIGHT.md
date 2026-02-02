# Playwright 测试框架安装指南

## 快速开始

### 1. 安装 Playwright

在 `frontend/` 目录下运行：

```bash
npm install -D @playwright/test
```

### 2. 安装浏览器

```bash
npx playwright install
```

### 3. 更新 package.json 脚本

在你的 `frontend/package.json` 中添加以下脚本：

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix --ignore-path .gitignore",

    "===== 测试脚本 =====",
    "test": "playwright test",
    "test:ui": "playwright test --ui",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug",
    "test:report": "playwright show-report"
  }
}
```

### 4. 安装完整依赖

```bash
npm install
```

## 验证安装

运行以下命令验证 Playwright 是否正确安装：

```bash
npx playwright --version
```

应该显示版本号，例如：`Version 1.40.0`

## 首次运行测试

### 选项 1: 自动启动开发服务器

测试配置已包含自动启动开发服务器，直接运行：

```bash
npm run test
```

### 选项 2: 手动启动开发服务器

在两个终端中分别运行：

**终端 1 - 启动前端开发服务器：**
```bash
cd frontend
npm run dev
```

**终端 2 - 启动后端服务器：**
```bash
cd backend
python manage.py runserver
```

**终端 3 - 运行测试：**
```bash
cd frontend
npm run test
```

## 运行特定测试

```bash
# 只运行产品管理测试
npm run test -- e2e/products.spec.ts

# 只运行包含"创建产品"的测试
npm run test -- -g "创建产品"

# 在 Chromium 浏览器中运行
npm run test -- --project=chromium

# 显示浏览器运行（适合调试）
npm run test:headed
```

## 调试测试

### 使用 Playwright UI（推荐）

```bash
npm run test:ui
```

这将打开一个可视化界面，你可以：
- 查看所有测试
- 运行单个测试
- 查看测试截图和视频
- 时间旅行调试

### 使用调试模式

```bash
npm run test:debug
```

这将打开浏览器并暂停执行，允许你逐步调试。

### 在代码中暂停

在测试代码中添加 `await page.pause()`：

```typescript
test('示例测试', async ({ page }) => {
  await page.goto('/products');
  await page.pause(); // 在此处暂停，打开调试器
  await page.click('button:has-text("创建产品")');
});
```

## 查看测试报告

测试运行后，查看 HTML 报告：

```bash
npm run test:report
```

或者在测试完成后自动打开报告（在 `playwright.config.ts` 中配置）。

## 故障排除

### 问题 1: 浏览器未安装

**错误信息：**
```
Executable doesn't exist at /path/to/browsers
```

**解决方案：**
```bash
npx playwright install
```

### 问题 2: 端口已被占用

**错误信息：**
```
Error: listen EADDRINUSE: address already in use :::5173
```

**解决方案：**
- 关闭正在运行的开发服务器
- 或者在不同端口运行：`npm run dev -- --port 3000`

### 问题 3: 测试超时

**解决方案：**

在 `playwright.config.ts` 中增加超时时间：

```typescript
export default defineConfig({
  timeout: 60000, // 60秒
  use: {
    actionTimeout: 20000,
  },
});
```

### 问题 4: 元素未找到

**解决方案：**

1. 增加等待时间：
```typescript
await page.waitForSelector('.my-element', { timeout: 10000 });
```

2. 使用更稳定的选择器：
```typescript
// 不好：依赖文本内容
page.locator('text=Submit')

// 好：使用 data-testid
page.locator('[data-testid="submit-button"]')
```

### 问题 5: 视频或截图失败

**解决方案：**

确保系统已安装必要的依赖：

**Linux (Ubuntu/Debian):**
```bash
npx playwright install-deps
```

**macOS:**
通常不需要额外依赖

**Windows:**
确保已安装 [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## 下一步

1. ✅ 安装完成
2. 📖 阅读 `e2e/README.md` 了解测试用例
3. 🧪 运行 `npm run test` 执行测试
4. 🎯 编写你的第一个测试用例
5. 🔄 配置 CI/CD 集成

## 需要帮助？

- [Playwright 官方文档](https://playwright.dev/)
- [Playwright GitHub Issues](https://github.com/microsoft/playwright/issues)
- [Playwright Discord 社区](https://aka.ms/playwright/discord)
