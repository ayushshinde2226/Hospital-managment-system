import sqlite3, os, time

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "performance_demo.db")
conn = sqlite3.connect(DB)

queries = [
    ("Total events", "SELECT COUNT(*) FROM benchmark_events", ()),
    ("Events by entity", "SELECT entity_type, COUNT(*) FROM benchmark_events GROUP BY entity_type ORDER BY 2 DESC", ()),
    ("Indexed entity lookup", "SELECT * FROM benchmark_events WHERE entity_type=? AND entity_id=? LIMIT 20", ("BILL", 1234)),
    ("Events by month", "SELECT substr(event_date,1,7) AS month, COUNT(*) FROM benchmark_events GROUP BY month ORDER BY month", ())
]
for label, sql, params in queries:
    t = time.perf_counter()
    rows = conn.execute(sql, params).fetchall()
    elapsed = (time.perf_counter() - t) * 1000
    print(f"{label}: {elapsed:.2f} ms | rows={len(rows)}")
conn.close()
