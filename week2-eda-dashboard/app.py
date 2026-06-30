"""
Cardiovascular Disease Dataset — Interactive EDA Dashboard
Author: Hamna Sajid
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import warnings
import os

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cardiovascular Disease EDA Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME — same palette family as Week 1 project for visual consistency
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #FFF1D3; color: #5D1C6A; }
    [data-testid="stSidebar"] { background-color: #5D1C6A !important; }
    [data-testid="stSidebar"] * { color: #FFF1D3 !important; }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"],
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
        background-color: #7A2880 !important;
        border: 1px solid #CA5995 !important;
        border-radius: 6px;
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: #CA5995 !important; color: #FFF1D3 !important;
    }
    [data-testid="stSidebar"] hr { border-color: #CA5995 !important; opacity: 0.4; }
    [data-testid="metric-container"] {
        background: #FFB090; border-radius: 12px; padding: 16px 20px;
    }
    [data-testid="metric-container"] * { color: #5D1C6A !important; }
    .section-header {
        font-size: 1.15rem; font-weight: 700; color: #5D1C6A;
        border-left: 4px solid #CA5995; padding-left: 10px;
        margin: 1.5rem 0 0.8rem 0;
    }
    .insight-box {
        background: #FFE4C4; border: 1.5px solid #CA5995; border-radius: 10px;
        padding: 14px 18px; margin: 6px 0; font-size: 0.92rem;
        color: #5D1C6A; line-height: 1.6;
    }
    .clean-step {
        background: #FFF8EE; border-left: 3px solid #FFB090; border-radius: 6px;
        padding: 10px 14px; margin: 5px 0; font-size: 0.88rem; color: #5D1C6A;
    }
    [data-testid="stExpander"] { border: 1px solid #FFB090 !important; background: #FFF8EE; }
    hr { border-color: #FFB090 !important; }
    h1, h2, h3, h4 { color: #5D1C6A !important; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

PALETTE    = ["#CA5995", "#FFB090", "#5D1C6A", "#7A2880", "#FF8C69", "#E07050"]
SEQ_SCALE  = ["#FFF1D3", "#FFB090", "#CA5995", "#7A2880", "#5D1C6A"]
PLOT_BG    = "#FFF8EE"


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="Loading dataset…")
def load_data(filepath: str) -> pd.DataFrame:
    """
    Load the cardiovascular disease dataset.

    Parameters
    ----------
    filepath : str
        Path to the dataset CSV file. Note: the real Kaggle file is
        semicolon-delimited, not comma-delimited.

    Returns
    -------
    pandas.DataFrame
        The raw, unprocessed dataset.
    """
    df = pd.read_csv(filepath, sep=";")
    return df


@st.cache_data(show_spinner="Cleaning data…")
def clean_data(df: pd.DataFrame):
    """
    Run the full data cleaning pipeline.

    Removes duplicates, converts age to years, imputes missing numeric
    values, drops physiologically impossible blood pressure readings,
    clips height/weight outliers, engineers a BMI column, and maps
    categorical codes to readable labels.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw dataset as loaded by `load_data`.

    Returns
    -------
    cleaned_df : pandas.DataFrame
        The cleaned dataset with derived columns added.
    cleaning_log : list of str
        Human-readable description of each cleaning step performed,
        used to populate the 'Data Cleaning Section' of the dashboard.
    """
    df = df.copy()
    log = []

    # ── 1. Record initial shape ──────────────────────────────────────────────
    initial_rows = len(df)

    # ── 2. Remove exact duplicate rows ───────────────────────────────────────
    dup_count = df.duplicated().sum()
    df = df.drop_duplicates()
    log.append(f"Removed {dup_count} exact duplicate rows.")

    # ── 3. Convert age from days to years (raw dataset stores age in days) ──
    if "age" in df.columns:
        df["age_years"] = (df["age"] / 365).round(0).astype(int)
        log.append("Converted 'age' from days to years (new column: age_years).")

    # ── 4. Handle missing values — numeric columns imputed with median ──────
    numeric_cols = ["height", "weight", "ap_hi", "ap_lo"]
    missing_before = df[numeric_cols].isnull().sum().sum()
    for col in numeric_cols:
        if col in df.columns and df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    log.append(f"Filled {int(missing_before)} missing numeric values using column median.")

    # ── 5. Fix inconsistent / impossible data types & ranges ─────────────────
    # Blood pressure: physiologically impossible values treated as outliers
    bp_outliers = (
        (df["ap_hi"] <= 0) | (df["ap_hi"] > 250) |
        (df["ap_lo"] <= 0) | (df["ap_lo"] > 200) |
        (df["ap_lo"] >= df["ap_hi"])
    )
    bp_outlier_count = bp_outliers.sum()
    df = df[~bp_outliers]
    log.append(
        f"Removed {bp_outlier_count} rows with physiologically impossible "
        f"blood pressure values (e.g. ap_hi ≤ 0, ap_lo ≥ ap_hi)."
    )

    # ── 6. Height / weight outlier treatment (IQR method) ────────────────────
    for col in ["height", "weight"]:
        Q1, Q3 = df[col].quantile([0.01, 0.99])
        before = len(df)
        df = df[(df[col] >= Q1) & (df[col] <= Q3)]
        removed = before - len(df)
        if removed > 0:
            log.append(f"Removed {removed} extreme outliers in '{col}' (1st–99th percentile clip).")

    # ── 7. Compute BMI — derived feature useful for analysis ─────────────────
    df["bmi"] = (df["weight"] / ((df["height"] / 100) ** 2)).round(1)
    log.append("Engineered new feature: BMI = weight(kg) / height(m)².")

    # ── 8. Map categorical codes to readable labels ──────────────────────────
    df["gender_label"]      = df["gender"].map({1: "Female", 2: "Male"})
    df["cholesterol_label"] = df["cholesterol"].map({1: "Normal", 2: "Above Normal", 3: "Well Above Normal"})
    df["gluc_label"]        = df["gluc"].map({1: "Normal", 2: "Above Normal", 3: "Well Above Normal"})
    df["cardio_label"]      = df["cardio"].map({0: "No Disease", 1: "Has Disease"})
    log.append("Mapped numeric category codes (gender, cholesterol, glucose, cardio) to readable labels.")

    # ── 9. Final shape summary ───────────────────────────────────────────────
    final_rows = len(df)
    log.append(f"Final dataset: {final_rows:,} rows retained from {initial_rows:,} original rows "
               f"({initial_rows - final_rows:,} removed, {(final_rows/initial_rows*100):.1f}% retained).")

    df.reset_index(drop=True, inplace=True)
    return df, log


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
default_path = "week2-eda-dashboard/dataset.csv"

with st.sidebar:
    st.markdown(
        '<svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="22" cy="22" r="20" fill="#CA5995"/>'
        '<path d="M22 32 L13 22 C9 18 9 12 14 10 C18 8 21 11 22 14 '
        'C23 11 26 8 30 10 C35 12 35 18 31 22 Z" fill="#FFF1D3"/>'
        '</svg>',
        unsafe_allow_html=True,
    )
    st.title("Cardio EDA")
    st.caption("Cardiovascular Disease Dashboard")
    st.divider()

    data_path = st.text_input("Path to dataset.csv", value=default_path)

if not os.path.exists(data_path):
    st.title("Cardiovascular Disease EDA Dashboard")
    st.markdown(
        '<div class="insight-box"><strong>Dataset not found.</strong> '
        'Place <code>dataset.csv</code> in the project root, or download the full '
        '70,000-row version from Kaggle (link in README) and update the sidebar path.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

raw_df = load_data(data_path)
df, cleaning_log = clean_data(raw_df)

# ── Sidebar filters — populated AFTER cleaning so options are real ───────────
with st.sidebar:
    st.divider()
    st.markdown("**Filters**")

    gender_filter = st.multiselect(
        "Gender", options=sorted(df["gender_label"].unique()),
        default=sorted(df["gender_label"].unique()),
    )
    cholesterol_filter = st.multiselect(
        "Cholesterol level", options=["Normal", "Above Normal", "Well Above Normal"],
        default=["Normal", "Above Normal", "Well Above Normal"],
    )
    age_range = st.slider(
        "Age range (years)",
        int(df["age_years"].min()), int(df["age_years"].max()),
        (int(df["age_years"].min()), int(df["age_years"].max())),
    )
    active_filter = st.selectbox(
        "Physical activity", options=["All", "Active only", "Inactive only"],
    )

    st.divider()
    st.markdown("**Column selection (for charts)**")
    numeric_options = ["age_years", "height", "weight", "bmi", "ap_hi", "ap_lo"]
    chart_x = st.selectbox("X-axis variable", numeric_options, index=0)
    chart_y = st.selectbox("Y-axis variable", numeric_options, index=4)

    st.divider()
    st.caption(f"{len(df):,} rows after cleaning")

# ── Apply filters ──────────────────────────────────────────────────────────────
mask = (
    df["gender_label"].isin(gender_filter) &
    df["cholesterol_label"].isin(cholesterol_filter) &
    df["age_years"].between(age_range[0], age_range[1])
)
if active_filter == "Active only":
    mask &= df["active"] == 1
elif active_filter == "Inactive only":
    mask &= df["active"] == 0

fdf = df[mask].copy()


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("Cardiovascular Disease — EDA Dashboard")
st.markdown(
    "Exploratory analysis of patient health records to identify patterns "
    "associated with cardiovascular disease risk."
)
st.divider()


# ─────────────────────────────────────────────
# SECTION 1 — DATASET OVERVIEW
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Dataset Overview</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows (raw)", f"{len(raw_df):,}")
c2.metric("Rows (cleaned & filtered)", f"{len(fdf):,}")
c3.metric("Columns (raw)", f"{raw_df.shape[1]}")
c4.metric("Cardio-positive rate", f"{fdf['cardio'].mean()*100:.1f}%")

with st.expander("Sample records (first 10 rows)"):
    st.dataframe(fdf.head(10), use_container_width=True)

with st.expander("Column names & data types"):
    dtypes_df = pd.DataFrame({
        "Column": raw_df.columns,
        "Data type": raw_df.dtypes.astype(str).values,
    })
    st.dataframe(dtypes_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# SECTION 2 — DATA CLEANING
# ─────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Data Cleaning Section</div>', unsafe_allow_html=True)

col_clean1, col_clean2 = st.columns([1, 1])

with col_clean1:
    st.markdown("**Missing value analysis (before cleaning)**")
    miss = raw_df.isnull().sum().reset_index()
    miss.columns = ["Column", "Missing values"]
    miss["% missing"] = (miss["Missing values"] / len(raw_df) * 100).round(2)
    miss = miss[miss["Missing values"] > 0].sort_values("% missing", ascending=False)
    if len(miss):
        st.dataframe(miss, use_container_width=True, hide_index=True)
    else:
        st.info("No missing values detected in raw data.")

with col_clean2:
    st.markdown("**Duplicate records analysis**")
    dup_count = raw_df.duplicated().sum()
    st.metric("Exact duplicate rows found", f"{dup_count:,}")
    st.metric("% of dataset", f"{dup_count/len(raw_df)*100:.2f}%")

st.markdown("**Summary of cleaning steps performed**")
for i, step in enumerate(cleaning_log, 1):
    st.markdown(f'<div class="clean-step">Step {i}: {step}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SECTION 3 — EXPLORATORY ANALYSIS
# ─────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Exploratory Analysis</div>', unsafe_allow_html=True)

# ── Statistical summary ──────────────────────────────────────────────────────
st.markdown("**Statistical summary**")
summary_cols = ["age_years", "height", "weight", "bmi", "ap_hi", "ap_lo"]
st.dataframe(fdf[summary_cols].describe().round(2), use_container_width=True)

# ── Univariate: Histogram ────────────────────────────────────────────────────
st.markdown("#### Distribution analysis (Histogram)")
hist_col = st.selectbox("Choose a variable to inspect its distribution",
                        numeric_options, index=0, key="hist_select")
fig_hist = px.histogram(
    fdf, x=hist_col, nbins=40, color="cardio_label",
    color_discrete_sequence=PALETTE,
    labels={hist_col: hist_col, "cardio_label": "Diagnosis"},
    template="plotly_white", marginal="box",
)
fig_hist.update_layout(height=420, margin=dict(l=0, r=0, t=20, b=20),
                       plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
                       legend=dict(orientation="h", y=1.05))
st.plotly_chart(fig_hist, use_container_width=True)

# ── Bivariate: Scatter ───────────────────────────────────────────────────────
st.markdown(f"#### Bivariate analysis — {chart_x} vs {chart_y} (Scatter Plot)")
sample_n = min(3000, len(fdf))
fig_scatter = px.scatter(
    fdf.sample(sample_n, random_state=42), x=chart_x, y=chart_y,
    color="cardio_label", opacity=0.5,
    color_discrete_sequence=PALETTE,
    labels={chart_x: chart_x, chart_y: chart_y, "cardio_label": "Diagnosis"},
    template="plotly_white",
)
fig_scatter.update_layout(height=440, margin=dict(l=0, r=0, t=20, b=20),
                          plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
st.plotly_chart(fig_scatter, use_container_width=True)

# ── Box plot: variable by cardio diagnosis ──────────────────────────────────
st.markdown("#### Box plot — variable distribution by diagnosis")
box_col = st.selectbox("Choose a variable", numeric_options, index=3, key="box_select")
fig_box = px.box(
    fdf, x="cardio_label", y=box_col, color="cardio_label",
    color_discrete_sequence=PALETTE,
    labels={"cardio_label": "Diagnosis", box_col: box_col},
    template="plotly_white",
)
fig_box.update_layout(showlegend=False, height=400, margin=dict(l=0, r=0, t=20, b=20),
                      plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
st.plotly_chart(fig_box, use_container_width=True)

# ── Correlation heatmap ──────────────────────────────────────────────────────
st.markdown("#### Correlation analysis")
corr_cols = ["age_years", "height", "weight", "bmi", "ap_hi", "ap_lo",
            "cholesterol", "gluc", "smoke", "alco", "active", "cardio"]
corr_matrix = fdf[corr_cols].corr().round(2)
fig_corr = px.imshow(
    corr_matrix, text_auto=True, color_continuous_scale=SEQ_SCALE,
    template="plotly_white", aspect="auto",
)
fig_corr.update_layout(height=500, margin=dict(l=0, r=0, t=20, b=20), paper_bgcolor=PLOT_BG)
st.plotly_chart(fig_corr, use_container_width=True)

# ── Bar chart: categorical breakdown ────────────────────────────────────────
st.markdown("#### Cardio disease rate by category (Bar Chart)")
cat_col = st.selectbox(
    "Choose a categorical variable",
    ["gender_label", "cholesterol_label", "gluc_label"], index=1, key="cat_select"
)
rate_by_cat = fdf.groupby(cat_col)["cardio"].mean().mul(100).round(1).reset_index()
fig_bar = px.bar(
    rate_by_cat, x=cat_col, y="cardio",
    color=cat_col, color_discrete_sequence=PALETTE,
    labels={"cardio": "Disease rate (%)", cat_col: cat_col},
    template="plotly_white",
)
fig_bar.update_layout(showlegend=False, height=380, margin=dict(l=0, r=0, t=20, b=20),
                      plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Line chart: trend across age ────────────────────────────────────────────
st.markdown("#### Disease rate trend across age (Line Chart)")
trend = fdf.groupby("age_years")["cardio"].mean().mul(100).round(1).reset_index()
fig_line = px.line(
    trend, x="age_years", y="cardio", markers=True,
    color_discrete_sequence=["#5D1C6A"],
    labels={"age_years": "Age (years)", "cardio": "Disease rate (%)"},
    template="plotly_white",
)
fig_line.update_traces(line=dict(width=3), marker=dict(size=6, color="#CA5995"))
fig_line.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=20),
                       plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
st.plotly_chart(fig_line, use_container_width=True)


# ─────────────────────────────────────────────
# SECTION 4 — INSIGHTS
# ─────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Key Insights & Recommendations</div>', unsafe_allow_html=True)

# Dynamically compute a few real insights from filtered data
strongest_corr = corr_matrix["cardio"].drop("cardio").abs().sort_values(ascending=False)
top_factor = strongest_corr.index[0]
top_factor_val = corr_matrix.loc["cardio", top_factor]

high_chol_rate = fdf[fdf["cholesterol_label"] == "Well Above Normal"]["cardio"].mean() * 100
normal_chol_rate = fdf[fdf["cholesterol_label"] == "Normal"]["cardio"].mean() * 100

active_rate = fdf[fdf["active"] == 1]["cardio"].mean() * 100
inactive_rate = fdf[fdf["active"] == 0]["cardio"].mean() * 100

insights = [
    f"<strong>{top_factor}</strong> shows the strongest correlation with cardiovascular "
    f"disease in this filtered sample (correlation = {top_factor_val:.2f}), making it the "
    "most informative single predictor among the variables analyzed.",

    f"Patients with <strong>well-above-normal cholesterol</strong> show a "
    f"<strong>{high_chol_rate:.1f}%</strong> disease rate, compared to "
    f"<strong>{normal_chol_rate:.1f}%</strong> for those with normal cholesterol — "
    "a clear, actionable risk signal.",

    f"Physically <strong>active</strong> patients show a <strong>{active_rate:.1f}%</strong> "
    f"disease rate versus <strong>{inactive_rate:.1f}%</strong> for inactive patients, "
    "reinforcing exercise as a protective factor.",

    "Disease rate rises steadily with age, consistent with established cardiovascular "
    "risk literature — there is no sharp threshold, but a gradual increase across the "
    "age range observed.",

    "<strong>Recommendation:</strong> Screening programs could prioritize patients with "
    "the combination of elevated cholesterol and low physical activity, as this profile "
    "shows the highest compounded risk in the dataset.",
]

for ins in insights:
    st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption(
    "Dataset: Cardiovascular Disease Dataset (sulianova, Kaggle) • "
    "Dashboard built with Streamlit, Pandas & Plotly • Week 2 Internship Project"
)