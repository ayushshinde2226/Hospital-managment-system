# Performance Benchmark Dataset

`performance_demo.db` is an intentionally large **synthetic** SQLite dataset for demonstrating DBMS indexing and query performance.

- Table: `benchmark_events`
- Rows: 540,000
- Approximate file size: 149.0 MB
- Indexes: `idx_bench_entity`, `idx_bench_date`
- Generated with a fixed seed for reproducibility.
- It contains no real patient data and is not used by the main application.

Example queries:
```sql
SELECT COUNT(*) FROM benchmark_events;
SELECT entity_type, COUNT(*) FROM benchmark_events GROUP BY entity_type;
SELECT * FROM benchmark_events WHERE entity_type='BILL' AND entity_id=1234 LIMIT 20;
SELECT substr(event_date,1,7) AS month, COUNT(*) FROM benchmark_events GROUP BY month ORDER BY month;
```

## Package Benchmark Asset
`benchmark_assets.bin` is a non-sensitive synthetic binary payload included only to keep the academic submission package above 100 MB as requested. It contains no real patient information and is not required for application execution.
