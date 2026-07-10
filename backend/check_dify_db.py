import asyncio, asyncpg, json

async def test():
    conn = await asyncpg.connect(host='127.0.0.1', port=5432, user='postgres', password='dh24681357', database='dify')
    rows = await conn.fetch("SELECT id, name, document_count FROM datasets ORDER BY created_at DESC")
    print(f"Datasets: {len(rows)}")
    for r in rows:
        print(f"  {r['name']} (docs={r['document_count']}) - {r['id']}")
    await conn.close()

asyncio.run(test())
