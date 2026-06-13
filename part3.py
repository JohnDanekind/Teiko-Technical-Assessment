import pandas as pd    
import matplotlib.pyplot as plt   
import sqlite3
import seaborn as sns
from scipy.stats import mannwhitneyu

conn = sqlite3.connect("clinical.db")

df = pd.read_sql_query("""
    SELECT 
        cc.sample_id,
        cc.population,
        cc.count,
        SUM(cc.count) OVER (PARTITION BY cc.sample_id) as total_count,
        ROUND(100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY cc.sample_id), 2) as percentage,
        s.treatment,
        s.response,
        s.sample_type,
        p.indication
    FROM cell_counts cc
    JOIN samples s ON cc.sample_id = s.sample_id
    JOIN patients p ON s.patient_id = p.patient_id
""", conn)

#print(df.head(5))
#print(df.columns.tolist())

conn.close()

df_part3 = df[
  (df["indication"] == "melanoma") & 
  (df["treatment"] == "miraclib") & 
  (df["sample_type"] == "PBMC") & 
  (df["response"].notna())               
  ]

#print(df_part3.shape)
#print(df_part3["response"].value_counts())
#df = pd.read_csv("summary_table.csv")

#print(df.head(5))

sns.boxplot(data=df_part3, x="population", y="percentage", hue="response")
plt.title("Cell Populatin Frequencies: Responders vs Non-Responders")
plt.xlabel("Cell Population")
plt.ylabel("Relative Frequency (%)")

plt.tight_layout()
plt.savefig("boxplot.png")
plt.show()

print("Saved boxplot.png")

populations = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

for cell in populations:
    responders = df_part3[(df_part3["response"] == "yes") & (df_part3["population"] == cell)]["percentage"]
    non_responders = df_part3[(df_part3["response"] == "no") & (df_part3["population"] == cell)]["percentage"]
    
    stat, p_value = mannwhitneyu(responders, non_responders, alternative="two-sided")
    significance = "SIGNIFICANT" if p_value < 0.05 else "not significant"
    print(f"{cell}: p={p_value:.4f} -> {significance}")
  