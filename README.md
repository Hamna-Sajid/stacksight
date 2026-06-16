# Stack Overflow Developer Survey 2024 — Analysis Dashboard

> An interactive Streamlit dashboard exploring developer trends, salaries, language popularity, remote work, and AI sentiment across 65 000+ survey responses.

---

## Objective

To perform exploratory data analysis (EDA) on the Stack Overflow Annual Developer Survey 2024, extract meaningful insights about the global developer landscape, and present findings through an interactive, user-friendly Streamlit dashboard.

---

## Dataset description

| Property | Detail |
|---|---|
| **Source** | [Stack Overflow Annual Developer Survey](https://survey.stackoverflow.co/) |
| **Year** | 2024 |
| **Respondents** | 65 437 |
| **Countries** | 177 |
| **Questions** | 114 columns |
| **License** | Open Database License (ODbL) |
| **Download** | [results.csv (direct)](https://github.com/StackExchange/Survey/raw/refs/heads/main/packages/archive/2024/results.csv) |

Key columns used in this project:

| Column | Description |
|---|---|
| `ConvertedCompYearly` | Annual compensation converted to USD |
| `YearsCodePro` | Years of professional coding experience |
| `LanguageHaveWorkedWith` | Programming languages used (semicolon-separated) |
| `RemoteWork` | Work arrangement (hybrid / remote / in-person) |
| `AISelect` | Whether the respondent uses AI coding tools |
| `AISent` | Sentiment toward AI development tools |
| `Country` | Country of residence |
| `EdLevel` | Highest level of formal education |
| `Employment` | Employment status |

---

## Technologies used

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Pandas | Data loading, cleaning, transformation |
| NumPy | Numerical operations |
| Plotly | Interactive charts |
| Matplotlib / Seaborn | Static charts (EDA notebook) |
| Streamlit | Dashboard framework |
| Jupyter Notebook | Exploratory analysis |

---

## Features

- **Dataset overview** — shape, missing values, raw data preview
- **Data summary** — salary and experience statistics
- **Sidebar filters** — filter by employment type, remote work, salary range
- **6 interactive visualizations:**
  - Horizontal bar chart — top 15 programming languages
  - Box plot — salary distribution by experience band
  - Pie chart — remote work split
  - Bar chart — AI sentiment breakdown
  - Scatter plot — salary vs experience coloured by remote arrangement
  - Bar chart — top 10 countries by respondent count
- **AI adoption deep-dive** — usage metrics + heatmap (AI use vs remote work)
- **Insights section** — dynamically computed key takeaways
- **EDA Jupyter Notebook** — full static analysis with Matplotlib/Seaborn

---

## Project structure

```
stacksight/
│
├── app.py                  ← Streamlit dashboard (main file)
├── results.csv             ← Dataset (download separately — see below)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
│
├── assets/
│   └── screenshots/        ← Dashboard screenshots
│
└── notebooks/
    └── analysis.ipynb      ← EDA notebook
```

---

## Installation guide

### 1. Clone the repository

```bash
git clone https://github.com/Hamna-Sajid/stacksight.git
cd stacksight
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Activate — Windows:
venv\Scripts\activate

# Activate — macOS / Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the dataset

```bash
# Option A — wget (Linux / macOS)
wget https://github.com/StackExchange/Survey/raw/refs/heads/main/packages/archive/2024/results.csv

# Option B — curl
curl -L -o results.csv https://github.com/StackExchange/Survey/raw/refs/heads/main/packages/archive/2024/results.csv

# Option C — browser
# Visit https://survey.stackoverflow.co/ → click Data (CSV) next to 2024
```

Place `results.csv` in the root of the project (same folder as `app.py`).

---

## Run the dashboard

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501` in your browser.

---

## Dashboard 

| Section | Preview |
|---|---|
| [Overview & metrics](assets/screenshots/Dataset%20overview.png) | ![Overview & metrics](assets/screenshots/Dataset%20overview.png) |
| [Language chart](assets/screenshots/Most-used%20programming%20languages.png) | ![Language chart](assets/screenshots/Most-used%20programming%20languages.png) |
| [Salary distribution by years of experience](assets/screenshots/Salary%20distribution%20by%20years%20of%20experience.png) | ![Salary distribution by years of experience](assets/screenshots/Salary%20distribution%20by%20years%20of%20experience.png) |
| [Remote work & AI sentiment](assets/screenshots/Remote%20work%20split%20%26%20AI%20sentiment.png) | ![Remote work & AI sentiment](assets/screenshots/Remote%20work%20split%20%26%20AI%20sentiment.png) |
| [Salary vs years of professional coding](assets/screenshots/Salary%20vs%20years%20of%20professional%20coding.png) | ![Salary vs years of professional coding](assets/screenshots/Salary%20vs%20years%20of%20professional%20coding.png) |
| [Top 10 countries by respondent count](assets/screenshots/Top%2010%20countries%20by%20respondent%20count.png) | ![Top 10 countries by respondent count](assets/screenshots/Top%2010%20countries%20by%20respondent%20count.png) |
| [AI tool usage vs remote work arrangement](assets/screenshots/AI%20tool%20usage%20vs%20remote%20work%20arrangement.png) | ![AI tool usage vs remote work arrangement](assets/screenshots/AI%20tool%20usage%20vs%20remote%20work%20arrangement.png) |

---

## Key insights

1. **JavaScript** remains the most-used language for the 12th consecutive year.
2. The **median global developer salary** is approximately $75 000 USD/year, with significant variance by country.
3. **Hybrid work** is now the dominant arrangement, surpassing both fully remote and in-person models.
4. Over **75%** of respondents currently use or are considering AI coding tools.
5. Salary grows steeply with experience — developers with 10+ years earn roughly 2–3× those with under 2 years.

---

## GitHub repository

[https://github.com/Hamna-Sajid/stacksight.git](https://github.com/Hamna-Sajid/stacksight.git)



## Author

**Hamna Sajid**  
