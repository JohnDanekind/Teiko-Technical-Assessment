# Teiko Technical Assessment
By John Danekind

This is my attempt at Teiko's take home technical assessment. 

## Setup

### Prerequisites
- Python 3.12
- macOS or Linux (tested on macOS)

### Create Virtual Environment

```bash
python3.12 -m venv teiko_technical
source teiko_technical/bin/activate
```

### Install Dependencies

```bash
make setup
```

### Run the Full Pipeline

```bash
make pipeline
```

This will:
1. Initialize the SQLite database and load all data from `cell-count.csv`
2. Generate the frequency summary table (`summary_table.csv`)
3. Generate the boxplot (`boxplot.png`)
4. Run statistical analysis and print results
5. Print Part 4 subset breakdowns

### Launch the Dashboard Locally

```bash
make dashboard
```

Opens the Streamlit dashboard at `http://localhost:8501`

## Live Dashboard

https://teiko-technical-assessment-kaye6efaw9c3qvgvjrbdpy.streamlit.app/

---

## Database Schema

The data is stored in a SQLite database (`clinical.db`) with four tables:

### projects
| Column | Type | Constraints |
|--------|------|-------------|
| project_id | TEXT | PRIMARY KEY |

### patients
| Column | Type | Constraints |
|--------|------|-------------|
| patient_id | TEXT | PRIMARY KEY |
| project_id | TEXT | FK → projects |
| age | INTEGER | |
| sex | TEXT | |
| indication | TEXT | |

### samples
| Column | Type | Constraints |
|--------|------|-------------|
| sample_id | TEXT | PRIMARY KEY |
| patient_id | TEXT | FK → patients |
| sample_type | TEXT | |
| treatment | TEXT | |
| response | TEXT | nullable |
| time_from_treatment_start | INTEGER | |

### cell_counts
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| sample_id | TEXT | FK → samples |
| population | TEXT | |
| count | INTEGER | |

### Rationale 

The schema I used normalizes the raw CSV data across four tables, separating biological
entities (projects, patients, samples) from measurements (cell_counts).

The Patient-level attributes like age, sex, and indication are stored once on the patients table rather than repeated on every sample row. 

This avoids redundancy and ensures consistency.If a patient attribute needs to be updated, it only changes in one place. 

Cell counts are stored in long format meaning  one row per population per sample. I did this instead of storing five separate columns because it makes queries simpler and adding new cell populations in the future wouldn't require schema changes. 

### Scalability 
This design would be easy to scale up for hundreds or thousands of samples:

- New projects and patients are added as just new rows which means no schema changes are needed
- New cell populations are new rows in `cell_counts`, not new columns
- The foreign key structure keeps joins efficient and data consistent
- Adding indexes on `sample_id` and `patient_id` in `cell_counts` and `samples`
  would significantly speed up queries at large scale
- If the dataset grew to millions of rows, the same schema would work in another standard SQL database like PostgreSQL or MySQL 


## Code Structure 
load_data.py is used to initialize the SQLite database and loads cell-count.csv. 
- It handles deduplication of data and it transforms the cell counts from wide (csv format) to long (database format) using pandas melt API. 


pipeline.py is used to run the full analysis sequentially: 

- In part 2, I compute relative frequency of each cell population per sample and save it to summary_table.csv 

- In part 3, I filter table to melanoma, miraclib, and PBMC. I then generate a boxplot and run Mann-Whitney U tests per population. 

- In Part 4: I query baseline samples and report information on questions covered in instructions document. 

app.py is my Streamlit dashboard that displays all results interactively. 

- It connects directly to the SQLite database and renders tables, the boxplot, and statistical results across three sections. 


In the Makefile, I have three targets: 
- setup installs dependencies, 
- pipeline runs the full analysis 
- dashboard launches Streamlit app. 

requirements.txt has all the Python dependencies. This includes pandas, matplotlib, seaborn, scipy, and streamlit. 

### Design Decisions

The pipeline is split into two scripts intentionally. `load_data.py` handles
the one-time database initialization and data loading. `pipeline.py` handles
all analysis. This allows the database to be rebuilt independently of the analysis and the analysis can be re-run without reloading the data.  

All analysis in `pipeline.py` flows from a single base SQL query that joins
`cell_counts`, `samples`, and `patients`. Parts 2 and 3 both use this same
dataframe, avoiding redundant database calls. Part 4 uses a separate targeted
query since it filters at the database level rather than in pandas.

---

## Key Findings

- 656 baseline melanoma PBMC samples treated with miraclib were identified
- `cd4_t_cell` was the only population with a statistically significant difference
  between responders and non-responders (p=0.0134, Mann-Whitney U test)
- Samples came from prj1 (384) and prj3 (272)
- 331 responders, 325 non-responders
- 344 males, 312 females
