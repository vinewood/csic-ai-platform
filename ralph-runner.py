#!/usr/bin/env python3
"""
Ralph Loop Runner — 中船党校前端迭代验证器
模拟 Ralph wiggumdev 循环：重置上下文 -> 执行 -> 验证 -> 存档经验 -> 循环
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime

try:
    import httpx
except ImportError:
    print("[RALPH] 正在安装 httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


RALPH_DIR = os.path.dirname(os.path.abspath(__file__))
PLANS_DIR = os.path.join(RALPH_DIR, ".plans")
PRD_PATH = os.path.join(PLANS_DIR, "PRD.md")
PROGRESS_PATH = os.path.join(PLANS_DIR, "progress.txt")

PAGES = {
    "/": "首页",
    "/login": "登录页",
    "/chat": "聊天页",
    "/workspace/teaching": "教学工作台",
    "/workspace/research": "科研工作台",
    "/workspace/news": "信息导航台",
    "/workspace/skills": "技能中心",
    "/workspace/video": "视频分析",
    "/workspace/admin": "管理后台",
    "/workspace/knowledge": "知识库",
}


def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[RALPH] [{timestamp}] {msg}")
    sys.stdout.flush()


def append_progress(entry: str):
    with open(PROGRESS_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{entry}\n")


async def check_page(client: httpx.AsyncClient, path: str, name: str) -> dict:
    try:
        resp = await client.get(f"http://localhost:8000{path}", timeout=5.0)
        html = resp.text
        has_html = "<html" in html or "<!DOCTYPE html" in html.upper()
        has_body = "<body" in html
        size = len(html)
        ok = resp.status_code == 200 and has_html and has_body and size > 1000
        return {"path": path, "name": name, "status": resp.status_code, "ok": ok, "size": size}
    except Exception as e:
        return {"path": path, "name": name, "status": 0, "ok": False, "size": 0, "error": str(e)}


async def run_iteration() -> tuple[bool, list]:
    log("--- 开始迭代检查 ---")
    async with httpx.AsyncClient(verify=False) as client:
        results = []
        for path, name in PAGES.items():
            result = await check_page(client, path, name)
            results.append(result)
            tag = "PASS" if result["ok"] else "FAIL"
            if result["ok"]:
                log(f"  [{tag}] {name} ({path}) - {result['status']} ({result['size']}B)")
            else:
                err = result.get("error", f"status={result['status']} size={result['size']}")
                log(f"  [{tag}] {name} ({path}) - {err}")

    all_pass = all(r["ok"] for r in results)
    return all_pass, results


async def main():
    log("=" * 60)
    log(" Ralph Loop Runner 启动")
    log(f" 项目: {RALPH_DIR}")
    log(f" PRD: {PRD_PATH}")
    log("=" * 60)

    # Check if server is running
    try:
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get("http://localhost:8000/", timeout=3.0)
            log(f" 服务状态: HTTP {resp.status_code}")
    except Exception:
        log(" 服务未运行! 正在尝试启动...")
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=RALPH_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        await asyncio.sleep(3)
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get("http://localhost:8000/", timeout=3.0)
                log(f" 服务已启动: HTTP {resp.status_code}")
        except Exception as e:
            log(f" 启动失败: {e}")
            log(" 请手动启动: cd csic-ai-platform && uvicorn main:app --port 8000")
            return

    max_iterations = 10
    for iteration in range(1, max_iterations + 1):
        log(f"\n--- 迭代 #{iteration}/{max_iterations} ---")

        all_pass, results = await run_iteration()
        passing = sum(1 for r in results if r["ok"])
        failing = sum(1 for r in results if not r["ok"])

        summary = f"- 迭代#{iteration}: {passing}/{len(results)} 页面通过"
        if not all_pass:
            failed = [r["name"] for r in results if not r["ok"]]
            summary += f"\n- 失败页面: {', '.join(failed)}"
        append_progress(summary)

        if all_pass:
            log(f"\n{'='*60}")
            log(f" [完成] 所有 {len(results)} 个页面检查通过!")
            log(f"{'='*60}")
            append_progress(f"\n- [完成] 所有页面正常，迭代完成!") 
            append_progress(f"\n<promise>COMPLETE</promise>")

            # Verify with ralph check
            ralph_bin = os.path.join(RALPH_DIR, "node_modules", "@wiggumdev", "ralph-windows-x64", "bin", "ralph.exe")
            if os.path.exists(ralph_bin):
                log(" 运行 ralph check 验证 PRD...")
                result = subprocess.run([ralph_bin, "check"], cwd=RALPH_DIR, capture_output=True, text=True)
                log(f" ralph check: {result.stdout.strip() or result.stderr.strip()}")
            break
        else:
            log(f"\n 警告: {failing} 个页面未通过")
            log(" 请修复后重新运行本脚本")
            break

    log(f"\n Ralph 循环结束")


if __name__ == "__main__":
    asyncio.run(main())
