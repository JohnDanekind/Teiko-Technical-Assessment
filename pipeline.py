import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu

# Establish database connection
conn = sqlite3.connect("clinical.db")

# Base query used for both Part 2 and Part 3.
# Joins cell_counts, samples, and patients so we have cell counts
# alongside sample metadata (treatment, response, sample_type) 
# and patient metadata (indication) in one dataframe.
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

# Part 2: Frequency Summary Table 

# Select only the columns required in instruction doc and save to csv 
# total_count and percentage are computed in the SQL query above using
# a window function that sums counts partitioned by sample.
print("=== Part 2: Frequency Summary Table ===")
summary_df = df[["sample_id", "population", "count", "total_count", "percentage"]]
summary_df.to_csv("summary_table.csv", index=False)
print(f"Saved {len(summary_df)} rows to summary_table.csv")

# Part 3: Statistical Analysis 

# Filter to only melanoma PBMC patients treated with miraclib.
# Drop rows where response is NaN (healthy/untreated patients have no response value).
print("\n=== Part 3: Statistical Analysis ===")
part3_df = df[
    (df["indication"] == "melanoma") &
    (df["treatment"] == "miraclib") &
    (df["sample_type"] == "PBMC") &
    (df["response"].notna())
]

# Boxplot comparing relative frequencies of each cell population
# between responders and non-responders.
sns.boxplot(data=part3_df, x="population", y="percentage", hue="response")
plt.title("Cell Population Frequencies: Responders vs Non-Responders")
plt.xlabel("Cell Population")
plt.ylabel("Relative Frequency (%)")
plt.tight_layout()
plt.savefig("boxplot.png")
plt.close()
print("Saved boxplot.png")

# For statistical analysis:

# Using Mann-Whitney U test for each cell population. (https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test)
# Tests whether responders and non-responders have significantly different relative frequencies. 
# Mann-Whitney doesn't assume the data is normally distributed unlike a normal t-test 
# Using a p-value of 0.05 as cutoff for statistical significance

populations = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
for cell in populations:
    responders = part3_df[(part3_df["response"] == "yes") & (part3_df["population"] == cell)]["percentage"]
    non_responders = part3_df[(part3_df["response"] == "no") & (part3_df["population"] == cell)]["percentage"]
    stat, p_value = mannwhitneyu(responders, non_responders, alternative="two-sided")
    significance = "SIGNIFICANT" if p_value < 0.05 else "not significant"
    print(f"{cell}: p={p_value:.4f} -> {significance}")

# Part 4: Subset Analysis 

# Query the DB directly to identify all melanoma PBMC samples at baseline
# (time_from_treatment_start = 0) from patients treated with miraclib.

print("\n=== Part 4: Subset Analysis ===")
part4_df = pd.read_sql_query("""
    SELECT
        s.sample_id,
        s.patient_id,
        s.treatment,
        s.response,
        s.sample_type,
        s.time_from_treatment_start,
        p.indication,
        p.sex,
        p.project_id
    FROM samples s
    JOIN patients p ON s.patient_id = p.patient_id
    WHERE p.indication = 'melanoma'
    AND s.sample_type = 'PBMC'
    AND s.time_from_treatment_start = 0
    AND s.treatment = 'miraclib'
""", conn)

# How many samples from each project
print("Samples per project:")
print(part4_df["project_id"].value_counts())

# How many subjects were responders vs non-responders
print("\nResponders vs Non-Responders:")
print(part4_df["response"].value_counts())

# How many subjects were male vs female
print("\nMales vs Females:")
print(part4_df["sex"].value_counts())




conn.close()