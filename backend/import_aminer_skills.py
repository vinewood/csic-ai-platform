"""Import AMiner skills to database"""
import sqlite3
conn = sqlite3.connect('/www/wwwroot/csic.thinkalike.com.cn/data/csic.db')

skills = [
    ('AMiner学术检索', '科研', 'Search', '6000万学者/3.3亿论文/1.8亿专利-AI科技情报挖掘', '#1677ff', 'https://open.aminer.cn', 0,
     '你是AMiner学术搜索集成专家。API: 学者搜索(person/search)、论文搜索(paper/search/pro需充值)、AI问答(paper/qa/search)、机构(org/search)、期刊(venue/search)、专利(patent/search)。5大工作流: 学者画像/论文深挖/机构分析/期刊论文/专利分析。认证: JWT HS256, Key=MTpI2JKWPNo1xQ==, UserID=6a50f0d66368530ed6f3aef7'),

    ('论文深度解读(AMiner)', '科研', 'Reading', '6维度结构化论文解读+AMiner交叉验证', '#10b981', 'https://open.aminer.cn', 0,
     '6维度分析论文:1背景与问题 2核心贡献与创新 3研究方法 4主要发现 5局限与改进 6AMiner验证(被引/相关论文 https://www.aminer.cn/pub/{paper_id})'),
]

for s in skills:
    row = conn.execute("SELECT id FROM skills WHERE name=?", (s[0],)).fetchone()
    if not row:
        conn.execute("INSERT INTO skills(name,category,icon,description,color,github_url,favorited,prompt) VALUES(?,?,?,?,?,?,?,?)", s)

conn.commit()
total = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
conn.close()
print(f"OK - {total} skills total")
