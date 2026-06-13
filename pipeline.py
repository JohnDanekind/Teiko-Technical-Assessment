import sqlite3
import pandas as pd

conn = sqlite3.connect("clinical.db")



# Select sample_id, population, and count
# Sum the counts of each sample_id and then add a percentage column showing relative frequency
df = pd.read_sql_query("""
    SELECT 
        cc.sample_id,
        cc.population,
        cc.count,
        SUM(cc.count) OVER (PARTITION BY cc.sample_id) as total_count,
        ROUND(100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY cc.sample_id), 2) as percentage
    FROM cell_counts cc
""", conn)

# Save to csv
df.to_csv("summary_table.csv", index=False)
print(f"Saved {len(df)} rows to summary_table.csv")
