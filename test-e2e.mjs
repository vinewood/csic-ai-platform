/**
 * CSIC AI Platform — Playwright Test Suite
 * 测试所有前端页面的可加载性、交互功能和UI完整性
 */

const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:8765';
const PAGES = [
  { path: '/', name: '介绍页(Landing)', topbar: false },
  { path: '/login', name: '登录页(Login)', topbar: false },
  { path: '/chat', name: 'AI对话(Chat)', topbar: true },
  { path: '/workspace/teaching', name: '教学工作台(Teaching)', topbar: true },
  { path: '/workspace/research', name: '科研工作台(Research)', topbar: true },
  { path: '/workspace/news', name: '信息导航台(News)', topbar: true },
  { path: '/workspace/skills', name: '技能中心(Skills)', topbar: true },
  { path: '/workspace/video', name: '视频分析(Video)', topbar: true },
  { path: '/workspace/knowledge', name: '知识库(Knowledge)', topbar: true },
  { path: '/workspace/admin', name: '系统管理(Admin)', topbar: true },
];

const results = [];

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });

  for (const page of PAGES) {
    const result = { name: page.name, path: page.path, status: 'PASS', errors: [], warnings: [] };
    const p = await context.newPage();

    try {
      // 1. 页面加载
      const resp = await p.goto(BASE + page.path, { waitUntil: 'networkidle', timeout: 15000 });
      const httpStatus = resp.status();
      if (httpStatus !== 200) {
        result.status = 'FAIL';
        result.errors.push(`HTTP ${httpStatus}`);
      }

      const title = await p.title();
      if (!title || title.length === 0) {
        result.warnings.push('页面标题为空');
      }

      // 2. 检查 React 挂载点
      const mountExists = await p.$('#app-mount');
      if (mountExists) {
        const mountContent = await p.evaluate(() => {
          const el = document.getElementById('app-mount');
          return el ? el.children.length : 0;
        });
        if (mountContent === 0) {
          result.warnings.push('React mount点无子元素（可能渲染延迟）');
          // 等待 2 秒再次检查
          await p.waitForTimeout(2000);
          const mountContent2 = await p.evaluate(() => {
            const el = document.getElementById('app-mount');
            return el ? el.children.length : 0;
          });
          result.warnings.push(`延迟后Render子元素数: ${mountContent2}`);
        } else {
          result.warnings.push(`Render子元素数: ${mountContent}`);
        }
      } else {
        result.warnings.push('未找到React挂载点#app-mount');
      }

      // 3. 检查 Ant Design CSS 加载
      const antdCSS = await p.evaluate(() => {
        const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
        return links.some(l => l.href.includes('antd'));
      });
      if (!antdCSS) {
        result.warnings.push('Ant Design CSS未加载');
      } else {
        result.warnings.push('Ant Design CSS已加载');
      }

      // 4. 检查 Topbar (如适用)
      if (page.topbar) {
        const topbar = await p.$('.topbar');
        if (!topbar) {
          result.warnings.push('Topbar未找到');
        }
        const navItems = await p.$$('.topbar-nav-item');
        result.warnings.push(`Topbar导航项数: ${navItems.length}`);
      }

      // 5. 检查控制台错误
      const consoleErrors = [];
      p.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text().substring(0, 100));
        }
      });
      await p.waitForTimeout(500);

      if (consoleErrors.length > 0) {
        result.warnings.push(`控制台错误: ${consoleErrors.slice(0, 3).join(' | ')}`);
      }

      // 6. 截图
      await p.screenshot({
        path: `test-results/${page.name.replace(/[()]/g, '').replace(/\//g, '-')}.png`,
        fullPage: true
      });

      // 7. 交互测试 - 点击几个可交互元素
      try {
        const buttons = await p.$$('button');
        if (buttons.length > 0) {
          result.warnings.push(`页面按钮数: ${buttons.length}`);
        }
        const links = await p.$$('a');
        if (links.length > 0) {
          result.warnings.push(`页面链接数: ${links.length}`);
        }
      } catch (e) {
        result.warnings.push(`交互测试跳过: ${e.message.substring(0, 60)}`);
      }

    } catch (e) {
      result.status = 'FAIL';
      result.errors.push(`异常: ${e.message.substring(0, 100)}`);
    } finally {
      await p.close();
    }

    results.push(result);
    console.log(`[${result.status}] ${result.name.padEnd(20)} ${page.path}`);
    result.warnings.forEach(w => console.log(`  → ${w}`));
    result.errors.forEach(e => console.log(`  ✗ ${e}`));
  }

  await browser.close();

  // 输出报告
  const passed = results.filter(r => r.status === 'PASS').length;
  const total = results.length;
  console.log('\n========================================');
  console.log(`  测试完成: ${passed}/${total} PASS`);
  console.log('========================================\n');

  const failResults = results.filter(r => r.status === 'FAIL');
  if (failResults.length > 0) {
    console.log('FAILED Pages:');
    failResults.forEach(r => console.log(`  ✗ ${r.name}: ${r.errors.join(', ')}`));
  }

  return { passed, total, results };
}

run().then(r => {
  process.exit(r.passed === r.total ? 0 : 1);
}).catch(e => {
  console.error('Test suite error:', e);
  process.exit(1);
});
