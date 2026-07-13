import sqlite3, re

def clean(text):
    if not text: return ""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</p>|</div>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;","&").replace("&lt;","<").replace("&gt;",">")
    text = re.sub(r"&[a-z]+;|&#?\w+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]

conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
rows = conn.execute("SELECT id, title, summary FROM news_articles").fetchall()
cleaned = 0
for row in rows:
    new_title = clean(row[1])
    new_summary = clean(row[2] or "")
    if new_title != row[1] or new_summary != (row[2] or ""):
        conn.execute("UPDATE news_articles SET title=?, summary=? WHERE id=?", (new_title, new_summary, row[0]))
        cleaned += 1
conn.commit()
print(f"Cleaned {cleaned}/{len(rows)}")
conn.close()
