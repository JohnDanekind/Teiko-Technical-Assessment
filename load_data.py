import sqlite3
import pandas as pd
import os

DB_PATH = "clinical.db"
CSV_PATH = "cell-count.csv"


def initialize_db(cursor):
    """Create all the tables for the database if they already exist."""

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS patients (
            patient_id  TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            age         INTEGER,
            sex         TEXT,
            indication  TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );

        CREATE TABLE IF NOT EXISTS samples (
            sample_id                  TEXT PRIMARY KEY,
            patient_id                 TEXT NOT NULL,
            sample_type                TEXT,
            treatment                  TEXT,
            response                   TEXT,
            time_from_treatment_start  INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );

        CREATE TABLE IF NOT EXISTS cell_counts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id   TEXT NOT NULL,
            population  TEXT NOT NULL,
            count       INTEGER NOT NULL,
            FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
        );
    """)
    print("Tables created.")


def load_data(cursor, csv_path):
    """Read in the CSV file and insert the data into all four of the tables"""

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}")

    
    # Load in projects 
    projects_df = df[["project"]].drop_duplicates().rename(
        columns={"project": "project_id"}
    )
    projects_df.to_sql("projects", cursor.connection, if_exists="append",
                       index=False)
    print(f"Inserted {len(projects_df)} projects.")

    # Load in patients 
    patients_df = (
        df[["subject", "project", "age", "sex", "condition"]]
        .drop_duplicates(subset=["subject"])
        .rename(columns={
            "subject":   "patient_id",
            "project":   "project_id",
            "condition": "indication", # TODO: consider this naming convention. It says indication in the document but I'm not sure if I want to rename it yet. 
        })
    )
    patients_df.to_sql("patients", cursor.connection, if_exists="append",
                       index=False)
    print(f"Inserted {len(patients_df)} patients.")

    # Load in samples
    samples_df = df[[
        "sample", "subject", "sample_type",
        "treatment", "response", "time_from_treatment_start"
    ]].rename(columns={
        "sample":  "sample_id",
        "subject": "patient_id",
    })
    samples_df.to_sql("samples", cursor.connection, if_exists="append",
                      index=False)
    print(f"Inserted {len(samples_df)} samples.")

    # Load Cell information 
    # Use df.melt to transform from csv format to database format (wide -> long)
    cell_counts_df = df.melt(
        id_vars=["sample"],
        value_vars=["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"],
        var_name="population",
        value_name="count",
    ).rename(columns={"sample": "sample_id"})
    
    print(cell_counts_df.shape)
    print(cell_counts_df.head(10))

    # Drop the auto-index; let SQLite assign the AUTOINCREMENT id
    cell_counts_df.to_sql("cell_counts", cursor.connection, if_exists="append",
                           index=False)
    print(f"Inserted {len(cell_counts_df)} cell count rows.")


def verify(cursor):
    """Print the row counts for every table to ensure everything is working correctly """
    print("\n── Verification -----------------------------------")
    for table in ("projects", "patients", "samples", "cell_counts"):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:15s}: {count:>7,} rows")
    print("-----------------------------------------------")


def main():
    # Remove stale DB so re-runs start clean
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        initialize_db(cursor)
        load_data(cursor, CSV_PATH)
        conn.commit()
        verify(cursor)

    print(f"\nDatabase ready: {DB_PATH}")


if __name__ == "__main__":
    main()