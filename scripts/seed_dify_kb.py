#!/usr/bin/env python3
"""Dify 知识库语料灌入脚本（仅服务器本地运行，2026-07-25 Kimi）

从权威公开来源抓取典型党校语料全文，清洗后经平台既有 kb_storage 管线入库
（txt 文件 + kb_documents 追踪表 + Dify PG 计数），检索即时生效。
仅使用标准库，无需安装依赖。

用法：ssh 到服务器后 `python3 seed_dify_kb.py`
"""
import html
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

DIFY_CONSOLE = "http://127.0.0.1:5001/console/api"

# (知识库ID, 文档名, 候选URL列表, 必含关键词, 最小字数)
DOCS = [
    # ── 党建知识库 ──
    ("aa5733e6-0a60-4426-921e-78d94a589f86", "中国共产党章程（二十大修订）", [
        "https://www.12371.cn/2022/10/26/ARTI1666788342244946.shtml",
    ], "总纲", 8000),
    ("aa5733e6-0a60-4426-921e-78d94a589f86", "中国共产党纪律处分条例（2023年修订）", [
        "https://jiwei.sta.edu.cn/b4/95/c4320a111765/page.htm",
        "https://bigdata.wuxi.gov.cn/doc/2023/12/28/4267379.shtml",
        "https://sjc.njtc.edu.cn/info/1086/5221.htm",
    ], "第一编", 10000),
    ("aa5733e6-0a60-4426-921e-78d94a589f86", "关于新形势下党内政治生活的若干准则", [
        "https://www.ytjgdj.gov.cn/art/2023/3/14/art_108340_2646.html",
        "https://news.12371.cn/2016/11/02/ARTI1478091665764299.shtm",
    ], "党内政治生活", 4000),
    # ── CSIC政策文件 ──
    ("9edffe23-5a26-4f1c-b165-4c40c791f644", "党的二十大报告全文", [
        "https://www.12371.cn/2022/10/25/ARTI1666705047474465.shtml",
        "http://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
    ], "中国式现代化", 20000),
    ("9edffe23-5a26-4f1c-b165-4c40c791f644", "二十届三中全会《中共中央关于进一步全面深化改革、推进中国式现代化的决定》", [
        "https://www.gov.cn/zhengce/202407/content_6963770.htm",
        "https://m-www.yvtc.edu.cn/news/show-13734.html",
    ], "全面深化改革", 10000),
    # ── 教学资源库 ──
    ("95a2b635-27f4-44ef-b2f3-dc04790dde02", "中国共产党党校（行政学院）工作条例（2025年修订）", [
        "http://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/202508/t20250812_1388239.html",
        "http://dangjian.people.com.cn/n1/2025/0812/c117092-40540529.html",
    ], "党校", 5000),
    # ── 船舶工程资料 ──
    ("562869af-5483-489c-a88d-b0fd4d7f49dc", "船舶制造业绿色发展行动纲要（2024—2030年）", [
        "https://wap.miit.gov.cn/zwgk/zcwj/wjfb/tz/art/2023/art_3c718652a49b4c0dbf8f2079567cb742.html",
        "http://china.cnsa.com.cn/newsinfo/7648521.html",
        "https://jasi.just.edu.cn/2024/0104/c6697a338180/page.htm",
    ], "绿色发展", 3000),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def html_to_text(page: str) -> str:
    page = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", page)
    # 段落级标签转换为换行，保住条文结构
    page = re.sub(r"(?i)</p>|<br\s*/?>|</div>|</h\d>|</li>|</tr>", "\n", page)
    text = re.sub(r"<[^>]+>", "", page)
    text = html.unescape(text)
    lines = [re.sub(r"[ \t\u3000]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def login(email: str, password: str) -> str:
    body = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(f"{DIFY_CONSOLE}/login", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
    token = (data.get("data") or {}).get("access_token", "")
    if not token:
        raise RuntimeError(f"Dify 登录失败: {str(data)[:200]}")
    return token


def create_doc(token: str, dataset_id: str, name: str, text: str) -> str:
    payload = {
        "name": name,
        "text": text,
        "indexing_technique": "high_quality",
        "process_rule": {"mode": "automatic"},
    }
    req = urllib.request.Request(
        f"{DIFY_CONSOLE}/datasets/{dataset_id}/document/create_by_text",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        doc = (data.get("document") or {})
        return f"OK doc_id={doc.get('id', '?')} tokens={doc.get('tokens', '?')}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read()[:200]}"
    except Exception as e:
        return f"ERROR {e}"


def main():
    # 复用平台既有的 kb_storage 管线：存 txt 文件 + kb_documents 追踪 + Dify PG 计数
    # （平台检索 retrieve_from_kb 是本地关键词匹配，语料落 txt 即生效）
    sys.path.insert(0, "/www/wwwroot/csic.thinkalike.com.cn/backend")
    from app.services.kb_storage import save_uploaded_doc

    ok, fail = 0, 0
    name_filter = sys.argv[1] if len(sys.argv) > 1 else ""
    for dataset_id, name, urls, keyword, min_len in DOCS:
        if name_filter and name_filter not in name:
            continue
        text, used_url = "", ""
        for url in urls:
            try:
                t = html_to_text(fetch_text(url))
                if keyword in t and len(t) >= min_len:
                    text, used_url = t, url
                    break
                print(f"  … 候选源内容不达标(len={len(t)}): {url[:70]}")
            except Exception as e:
                print(f"  … 候选源失败({type(e).__name__}): {url[:70]}")
        if not text:
            print(f"✘ {name}: 全部候选源均不可用，跳过")
            fail += 1
            continue
        try:
            info = save_uploaded_doc(dataset_id, name + ".txt", text.encode("utf-8"), "seed")
            print(f"✔ {name} <- {used_url[:60]} | {len(text)}字 | id={info['id'][:8]} status={info['status']}")
            ok += 1
        except Exception as e:
            print(f"✘ {name}: 入库失败 {e}")
            fail += 1
        time.sleep(1)

    print(f"\n完成：成功 {ok} / 失败 {fail}。检索走本地 kb_documents（status=ready 即时生效）。")


if __name__ == "__main__":
    main()
