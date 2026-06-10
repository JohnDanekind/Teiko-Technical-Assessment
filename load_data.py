import sqlite3
import pandas as pd  

# load csv 
df = pd.read_csv("cell-count.csv")

print(df.head(10))