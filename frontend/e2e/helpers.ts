import { Page, Locator } from '@playwright/test';

/**
 * 测试辅助函数
 * 提供常用的测试操作和数据
 */

/**
 * 登录辅助函数（如果系统有认证功能）
 */
export async function login(page: Page, username: string, password: string) {
  await page.goto('/login');

  await page.fill('input[name="username"], input[placeholder*="用户名"], input[placeholder*="账号"]', username);
  await page.fill('input[name="password"], input[placeholder*="密码"]', password);

  await page.click('button:has-text("登录"), button[type="submit"]');

  // 等待登录完成
  await page.waitForURL('**/dashboard', { timeout: 5000 });
}

/**
 * 等待加载完成
 */
export async function waitForLoading(page: Page) {
  try {
    await page.waitForSelector('.el-loading, .is-loading', { state: 'detached', timeout: 10000 });
  } catch (error) {
    // 如果没有加载元素，忽略错误
  }
}

/**
 * 等待消息提示
 */
export async function waitForMessage(page: Page, type: 'success' | 'error' | 'warning' | 'info' = 'success') {
  const messageSelector = `.el-message--${type}`;
  await page.waitForSelector(messageSelector, { state: 'visible', timeout: 5000 });
}

/**
 * 获取表格中的所有文本内容
 */
export async function getTableData(page: Page, tableSelector: string = '.el-table') {
  const table = page.locator(tableSelector);
  const rows = table.locator('.el-table__body-wrapper .el-table__row');

  const data: string[][] = [];

  const rowCount = await rows.count();
  for (let i = 0; i < rowCount; i++) {
    const row = rows.nth(i);
    const cells = row.locator('.cell, td');

    const rowData: string[] = [];
    const cellCount = await cells.count();

    for (let j = 0; j < cellCount; j++) {
      const cellText = await cells.nth(j).textContent();
      rowData.push(cellText?.trim() || '');
    }

    data.push(rowData);
  }

  return data;
}

/**
 * 选择下拉选项
 */
export async function selectOption(page: Page, selectSelector: string, optionText: string) {
  // 点击下拉框
  await page.click(selectSelector);

  // 等待下拉菜单出现
  await page.waitForSelector('.el-select-dropdown', { state: 'visible' });

  // 点击选项
  await page.click(`.el-select-dropdown__item:has-text("${optionText}")`);

  // 等待下拉菜单关闭
  await page.waitForSelector('.el-select-dropdown', { state: 'hidden', timeout: 5000 });
}

/**
 * 上传文件
 */
export async function uploadFile(page: Page, fileInputSelector: string, filePath: string) {
  const fileInput = page.locator(fileInputSelector);
  await fileInput.setInputFiles(filePath);
}

/**
 * 等待并确认对话框
 */
export async function confirmDialog(page: Page) {
  // 等待确认对话框出现
  await page.waitForSelector('.el-message-box', { state: 'visible' });

  // 点击确定按钮
  await page.click('.el-message-box__btnprimary, button:has-text("确定")');

  // 等待对话框关闭
  await page.waitForSelector('.el-message-box', { state: 'hidden', timeout: 5000 });
}

/**
 * 取消对话框
 */
export async function cancelDialog(page: Page) {
  // 等待对话框出现
  await page.waitForSelector('.el-message-box', { state: 'visible' });

  // 点击取消按钮
  await page.click('.el-message-box__btns button:nth-child(2), button:has-text("取消")');

  // 等待对话框关闭
  await page.waitForSelector('.el-message-box', { state: 'hidden', timeout: 5000 });
}

/**
 * 创建测试产品
 */
export async function createTestProduct(page: Page, productData: {
  name: string;
  vendor: string;
  type: string;
  description?: string;
}) {
  await page.goto('/products/create');

  // 填写表单
  await page.fill('input[placeholder*="产品名称"]', productData.name);
  await page.fill('input[placeholder*="厂商"]', productData.vendor);

  // 选择产品类型
  const typeSelect = page.locator('.product-form .el-select').first();
  await typeSelect.click();
  await page.locator(`.el-select-dropdown__item:has-text("${productData.type}")`).click();

  // 填写描述（可选）
  if (productData.description) {
    await page.fill('textarea[placeholder*="描述"]', productData.description);
  }

  // 提交
  await page.click('button:has-text("提交")');

  // 等待创建完成
  await waitForLoading(page);

  // 返回当前 URL（可能是产品详情页）
  return page.url();
}

/**
 * 创建测试需求
 */
export async function createTestRequirement(page: Page, requirementData: {
  title: string;
  description: string;
  filePath?: string;
}) {
  await page.goto('/requirements/create');

  // 填写标题
  await page.fill('input[placeholder*="标题"]', requirementData.title);

  if (requirementData.filePath) {
    // 切换到文件上传
    await page.click('text=文件上传, text=上传文件');

    // 上传文件
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(requirementData.filePath);
  } else {
    // 填写文本描述
    const textarea = page.locator('textarea[placeholder*="描述"], textarea[placeholder*="需求"]');
    await textarea.fill(requirementData.description);
  }

  // 提交
  await page.click('button:has-text("提交"), button:has-text("创建")');

  // 等待创建完成
  await waitForLoading(page);

  return page.url();
}

/**
 * 截图辅助函数（失败时使用）
 */
export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({
    path: `test-results/screenshots/${name}.png`,
    fullPage: true
  });
}

/**
 * 验证表格行数
 */
export async function expectTableRowCount(page: Page, tableSelector: string, count: number) {
  const rows = page.locator(`${tableSelector} .el-table__body-wrapper .el-table__row`);
  const actualCount = await rows.count();
  if (actualCount !== count) {
    throw new Error(`Expected ${count} rows, but found ${actualCount}`);
  }
}

/**
 * 清空输入框
 */
export async function clearInput(page: Page, selector: string) {
  const input = page.locator(selector);
  await input.click();
  await input.fill('');
}

/**
 * 等待 API 请求完成
 */
export async function waitForAPIResponse(page: Page, urlPattern: string) {
  return page.waitForResponse(
    (response) => response.url().includes(urlPattern),
    { timeout: 30000 }
  );
}

/**
 * 获取 Toast 消息文本
 */
export async function getToastMessage(page: Page): Promise<string> {
  const message = page.locator('.el-message__content, .el-notification__content');
  await message.waitFor({ state: 'visible', timeout: 5000 });
  return await message.textContent() || '';
}

/**
 * 检查元素是否存在
 */
export async function elementExists(page: Page, selector: string): Promise<boolean> {
  const count = await page.locator(selector).count();
  return count > 0;
}

/**
 * 安全点击（确保元素可见且可点击）
 */
export async function safeClick(page: Page, selector: string) {
  const element = page.locator(selector);

  // 等待元素可见
  await element.waitFor({ state: 'visible', timeout: 5000 });

  // 滚动到元素
  await element.scrollIntoViewIfNeeded();

  // 点击
  await element.click();
}

/**
 * 等待表格数据加载
 */
export async function waitForTableData(page: Page, tableSelector: string = '.el-table') {
  await page.waitForSelector(`${tableSelector} .el-table__body-wrapper .el-table__row`, {
    state: 'attached',
    timeout: 10000
  });
}

/**
 * 模拟用户输入（带延迟）
 */
export async function humanType(page: Page, selector: string, text: string, delay: number = 50) {
  const element = page.locator(selector);
  await element.click();

  for (const char of text) {
    await element.type(char, { delay });
  }
}

/**
 * 测试数据生成器
 */
export const TestDataGenerator = {
  /**
   * 生成随机产品名称
   */
  productName(): string {
    const adjectives = ['智能', '高效', '安全', '企业级', '云端', '自动化', '专业'];
    const nouns = ['防火墙', '网关', '检测系统', '分析平台', '管理工具', '防护系统'];

    const adj = adjectives[Math.floor(Math.random() * adjectives.length)];
    const noun = nouns[Math.floor(Math.random() * nouns.length)];

    return `${adj}${noun}_${Date.now()}`;
  },

  /**
   * 生成随机需求描述
   */
  requirementDescription(): string {
    const descriptions = [
      '需要支持防火墙功能，能够进行网络访问控制，支持入侵检测和防御。',
      '要求系统能够对大量日志数据进行实时分析，生成可视化报告。',
      '需要资产管理功能，支持自动发现和分类网络中的资产设备。',
      '要求支持威胁情报集成，能够自动更新和匹配最新的威胁信息。',
      '需要SOAR功能，支持自动化安全编排和响应。'
    ];

    return descriptions[Math.floor(Math.random() * descriptions.length)];
  },

  /**
   * 生成随机邮箱
   */
  email(): string {
    return `test${Date.now()}@example.com`;
  },

  /**
   * 生成随机手机号
   */
  phoneNumber(): string {
    return `138${Math.floor(Math.random() * 100000000).toString().padStart(8, '0')}`;
  },

  /**
   * 生成随机IP地址
   */
  ipAddress(): string {
    return `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
  }
};
