#!/usr/bin/env python3
"""CSIC AI Platform — Smoke Test Suite
快速验证所有前端页面 HTTP 200、HTML size 合理、关键标签存在"""

import sys
import time
import subprocess
import signal
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8765"
PAGES = [
    ("/", "介绍页(Landing)"),
    ("/login", "登录页(Login)"),
    ("/chat", "AI对话(Chat)"),
    ("/workspace/teaching", "教学工作台(Teaching)"),
    ("/workspace/research", "科研工作台(Research)"),
    ("/workspace/news", "信息导航台(News)"),
    ("/workspace/skills", "技能中心(Skills)"),
    ("/workspace/video", "视频分析(Video)"),
    ("/workspace/knowledge", "知识库(Knowledge)"),
    ("/workspace/admin", "系统管理(Admin)"),
]

def test_page(path, name):
    url = BASE + path
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            html = resp.read().decode("utf-8")
            size = len(html)
    except urllib.error.HTTPError as e:
        return {"name": name, "path": path, "status": "FAIL", "code": e.code, "size": 0, "errors": [f"HTTP {e.code}"]}
    except Exception as e:
        return {"name": name, "path": path, "status": "FAIL", "code": 0, "size": 0, "errors": [str(e)[:80]]}

    checks = []
    errors = []

    if status != 200:
        errors.append(f"HTTP {status}")
    if size < 500:
        errors.append(f"页面太小({size}B)")
    else:
        checks.append(f"{size}B")

    # Check for React mount point
    if 'app-mount' not in html:
        errors.append("缺少#app-mount")
    else:
        checks.append("有app-mount")

    # Check for Ant Design CSS
    if 'antd' not in html:
        errors.append("无AntD引用")
    else:
        checks.append("有AntD")

    # Check for Babel script
    if 'babel' not in html:
        errors.append("无Babel引用")
    else:
        checks.append("有Babel")

    # Check for mock-data
    if 'mock-data' not in html:
        errors.append("无mock-data")
    else:
        checks.append("有Mock")

    # Check page title
    if '<title>' not in html:
        errors.append("无title")

    ok = len(errors) == 0
    return {
        "name": name, "path": path, "status": "PASS" if ok else "FAIL",
        "code": status, "size": size, "checks": checks, "errors": errors
    }

def main():
    print("=" * 60)
    print("  中船党校 AI 平台 — 前端 Smoke Test")
    print(f"  目标: {BASE}")
    print("=" * 60)

    results = []
    for path, name in PAGES:
        result = test_page(path, name)
        results.append(result)
        print(f"\n{'✅' if result['status']=='PASS' else '❌'} {result['name']:22s} ({path})")
        print(f"   HTTP {result['code']} | {result['size']}B")
        if result.get('checks'):
            print(f"   {' | '.join(result['checks'])}")
        if result['errors']:
            for e in result['errors']:
                print(f"   ✗ {e}")

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    total = len(results)

    print("\n" + "=" * 60)
    print(f"  结果: {passed}/{total} 通过  {failed} 失败")
    print("=" * 60)

    # Generate report
    report_lines = [
        "# CSIC AI Platform — 前端 Smoke Test Report",
        f"\n> 测试时间: {time.strftime('%Y-%m-%d %H:%M')}",
        f"> 环境: Python Smoke Test",
        f"\n## 结果汇总",
        f"\n| 结果 | 数量 |",
        f"|------|------|",
        f"| 通过 | {passed} |",
        f"| 失败 | {failed} |",
        f"| 总计 | {total} |",
        f"\n## 逐项结果\n",
    ]
    for r in results:
        icon = "✅" if r['status'] == 'PASS' else "❌"
        report_lines.append(f"### {icon} {r['name']} (`{r['path']}`)")
        report_lines.append(f"- HTTP: {r['code']} | Size: {r['size']}B")
        if r.get('checks'):
            report_lines.append(f"- 检查: {' | '.join(r['checks'])}")
        if r['errors']:
            for e in r['errors']:
                report_lines.append(f"- ❌ {e}")
        report_lines.append("")

    report = "\n".join(report_lines)
    from pathlib import Path
    report_path = str(Path(__file__).parent / "test-results" / "smoke-test-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存: {report_path}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
