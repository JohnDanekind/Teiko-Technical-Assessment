import streamlit as st       
import sqlite3    
import pandas as pd  
import matplotlib.pyplot as plt          
import seaborn as sns 
from scipy.stats import mannwhitneyu


st.title("Teiko Clinical Trial Dashboard")

conn = sqlite3.connect("clinical.db")

# Part 2: Frequency Summary Table 
st.header("Part 2: Cell Population Frequencies")

summary_df = pd.read_sql_query("""
    SELECT 
        cc.sample_id,
        cc.population,
        cc.count,
        SUM(cc.count) OVER (PARTITION BY cc.sample_id) as total_count,
        ROUND(100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY cc.sample_id), 2) as percentage
    FROM cell_counts cc
""", conn)

st.dataframe(summary_df)



# Part 3: Statistical Analysis 
st.header("Part 3: Responders vs Non-Responders")

part3_df = pd.read_sql_query("""
    SELECT 
        cc.sample_id,
        cc.population,
        cc.count,
        ROUND(100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY cc.sample_id), 2) as percentage,
        s.treatment,
        s.response,
        s.sample_type,
        p.indication
    FROM cell_counts cc
    JOIN samples s ON cc.sample_id = s.sample_id
    JOIN patients p ON s.patient_id = p.patient_id
""", conn)

part3_df = part3_df[
    (part3_df["indication"] == "melanoma") &
    (part3_df["treatment"] == "miraclib") &
    (part3_df["sample_type"] == "PBMC") &
    (part3_df["response"].notna())
]

fig, ax = plt.subplots()
sns.boxplot(data=part3_df, x="population", y="percentage", hue="response", ax=ax)
ax.set_title("Cell Population Frequencies: Responders vs Non-Responders")
ax.set_xlabel("Cell Population")
ax.set_ylabel("Relative Frequency (%)")
st.pyplot(fig)

st.subheader("Statistical Significance (Mann-Whitney U Test)")

populations = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
results = []
for cell in populations:
    responders = part3_df[(part3_df["response"] == "yes") & (part3_df["population"] == cell)]["percentage"]
    non_responders = part3_df[(part3_df["response"] == "no") & (part3_df["population"] == cell)]["percentage"]
    stat, p_value = mannwhitneyu(responders, non_responders, alternative="two-sided")
    significance = "SIGNIFICANT" if p_value < 0.05 else "not significant"
    results.append({"population": cell, "p_value": round(p_value, 4), "result": significance})

results_df = pd.DataFrame(results)
st.dataframe(results_df)


# Part 4: Subset Analysis
st.header("Part 4: Baseline Melanoma PBMC Samples (Miraclib, Time=0)")

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

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Samples per Project")
    st.dataframe(part4_df["project_id"].value_counts().reset_index())

with col2:
    st.subheader("Responders vs Non-Responders")
    st.dataframe(part4_df["response"].value_counts().reset_index())

with col3:
    st.subheader("Males vs Females")
    st.dataframe(part4_df["sex"].value_counts().reset_index())


conn.close()