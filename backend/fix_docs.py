import sqlite3
conn = sqlite3.connect('/www/wwwroot/csic.thinkalike.com.cn/data/csic.db')
conn.execute("UPDATE kb_documents SET status='ready', progress=100")
conn.commit()
for r in conn.execute('SELECT name,status,progress FROM kb_documents').fetchall():
    print(r[0], r[1], r[2])
conn.close()
print("DONE")
