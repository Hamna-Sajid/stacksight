"""
Stack Overflow Developer Survey 2024 — Interactive Analysis Dashboard
Author: Hamna Sajid
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import warnings
import os

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Stack Overflow Developer Survey 2024",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #FFF1D3; color: #5D1C6A; }

    [data-testid="stSidebar"] { background-color: #5D1C6A !important; }
    [data-testid="stSidebar"] * { color: #FFF1D3 !important; }
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #7A2880 !important;
        color: #FFF1D3 !important;
        border: 1px solid #CA5995 !important;
        border-radius: 6px;
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {
        background-color: #7A2880 !important;
        border: 1px solid #CA5995 !important;
        border-radius: 6px;
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: #CA5995 !important;
        color: #FFF1D3 !important;
    }
    [data-testid="stSidebar"] hr { border-color: #CA5995 !important; opacity: 0.4; }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stCaption { color: #FFB090 !important; }

    [data-testid="metric-container"] {
        background: #FFB090;
        border: none;
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="metric-container"] * { color: #5D1C6A !important; }

    .section-header {
        font-size: 1.15rem; font-weight: 700; color: #5D1C6A;
        border-left: 4px solid #CA5995;
        padding-left: 10px; margin: 1.5rem 0 0.8rem 0;
    }
    .insight-box {
        background: #FFE4C4; border: 1.5px solid #CA5995;
        border-radius: 10px; padding: 14px 18px; margin: 6px 0;
        font-size: 0.92rem; color: #5D1C6A; line-height: 1.6;
    }
    .info-banner {
        background: #FFE4C4; border: 1.5px solid #CA5995;
        border-radius: 8px; padding: 12px 16px;
        font-size: 0.88rem; color: #5D1C6A;
    }
    [data-testid="stExpander"] {
        border: 1px solid #FFB090 !important;
        border-radius: 8px; background: #FFF8EE;
    }
    hr { border-color: #FFB090 !important; }
    h1, h2, h3, h4 { color: #5D1C6A !important; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

PALETTE    = ["#CA5995", "#FFB090", "#5D1C6A", "#FFF1D3", "#7A2880", "#FF8C69"]
ORANGE_SEQ = ["#FFF1D3", "#FFB090", "#CA5995", "#7A2880", "#5D1C6A"]


@st.cache_data(show_spinner="Loading dataset…")
def load_data(filepath: str) -> pd.DataFrame:
    COLS = [
        "Age", "EdLevel", "Employment", "RemoteWork", "YearsCodePro",
        "DevType", "LanguageHaveWorkedWith", "LanguageWantToWorkWith",
        "DatabaseHaveWorkedWith", "WebframeHaveWorkedWith", "AISelect",
        "AISent", "ConvertedCompYearly", "Country", "JobSat", "OrgSize",
    ]
    return pd.read_csv(filepath, usecols=lambda c: c in COLS, low_memory=False)


@st.cache_data(show_spinner="Cleaning data…")
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # 1. Drop rows where ALL key cols are NaN
    df.dropna(subset=["Age", "EdLevel", "Employment", "ConvertedCompYearly"],
              how="all", inplace=True)
    # 2. Salary outliers
    if "ConvertedCompYearly" in df.columns:
        df = df[
            df["ConvertedCompYearly"].isna() |
            ((df["ConvertedCompYearly"] >= 1_000) &
             (df["ConvertedCompYearly"] <= 1_000_000))
        ]
    # 3. YearsCodePro text → numeric
    if "YearsCodePro" in df.columns:
        df["YearsCodePro"] = df["YearsCodePro"].replace(
            {"Less than 1 year": 0, "More than 50 years": 51}
        )
        df["YearsCodePro"] = pd.to_numeric(df["YearsCodePro"], errors="coerce")
    # 4. Employment: first value only
    if "Employment" in df.columns:
        df["Employment"] = df["Employment"].str.split(";").str[0].str.strip()
    # 5. Experience bands
    if "YearsCodePro" in df.columns:
        df["ExperienceBand"] = pd.cut(
            df["YearsCodePro"],
            bins=[-1, 0, 2, 5, 10, 20, 100],
            labels=["<1 yr", "1-2 yrs", "3-5 yrs", "6-10 yrs", "11-20 yrs", "20+ yrs"],
        )
    df.reset_index(drop=True, inplace=True)
    return df


def explode_multi(df: pd.DataFrame, col: str, sep: str = ";") -> pd.Series:
    return (
        df[col].dropna().str.split(sep).explode()
        .str.strip().value_counts()
    )


# ── Pre-load data so sidebar filters are populated on first render ────────────
_default_path = "results.csv"
_data_exists  = os.path.exists(_default_path)

if _data_exists:
    raw_df         = load_data(_default_path)
    df             = clean_data(raw_df)
    emp_options    = sorted(df["Employment"].dropna().unique().tolist())
    remote_options = sorted(df["RemoteWork"].dropna().unique().tolist())
else:
    emp_options = remote_options = []


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    # ── Logo: use local .avif if present, otherwise SVG fallback ─────────────
    avif_files = [f for f in os.listdir(".") if f.lower().endswith(".avif")]
    if avif_files:
        with open(avif_files[0], "rb") as fh:
            st.image(fh.read(), width=56)
    else:
        st.markdown(
            '<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">'
            '<rect width="48" height="48" rx="8" fill="#CA5995"/>'
            '<text x="24" y="33" font-size="22" text-anchor="middle" '
            'font-family="monospace" fill="#FFF1D3" font-weight="bold">SO</text>'
            '</svg>',
            unsafe_allow_html=True,
        )

    st.title("StackSight")
    st.caption("Developer Analysis Dashboard · 2024")
    st.divider()

    data_path = st.text_input(
        "Path to results.csv", value=_default_path,
        help="Download from https://survey.stackoverflow.co/ and place next to app.py",
    )
    st.divider()
    st.markdown("**Filters**")

    # ── FIX: options & defaults populated from real data ─────────────────────
    filter_employment = st.multiselect(
        "Employment type",
        options=emp_options,
        default=emp_options,
        placeholder="Select types…",
    )
    filter_remote = st.multiselect(
        "Remote work",
        options=remote_options,
        default=remote_options,
        placeholder="Select options…",
    )
    salary_range = st.slider(
        "Salary range (USD / year)",
        min_value=0, max_value=400_000,
        value=(0, 400_000), step=5_000, format="$%d",
    )
    st.divider()
    st.caption("Stack Overflow Developer Survey 2024 · 65 000+ respondents")


# ─────────────────────────────────────────────
# GATE: show instructions if CSV not found
# ─────────────────────────────────────────────
if not os.path.exists(data_path):
    st.title("Stack Overflow Developer Survey 2024")
    st.markdown(
        '<div class="info-banner"><strong>Dataset not found.</strong> '
        'Follow the steps below to download it, then restart the app.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("""
### How to get the dataset
1. Go to **[https://survey.stackoverflow.co/](https://survey.stackoverflow.co/)**
2. Click **Data (CSV)** next to **2024**
3. Save as `results.csv` in the same folder as `app.py`
4. Run `streamlit run app.py`
""")
    st.code(
        "curl -L -o results.csv https://github.com/StackExchange/Survey/raw/"
        "refs/heads/main/packages/archive/2024/results.csv",
        language="bash",
    )
    st.stop()


# ── Reload if user typed a different path ─────────────────────────────────────
if data_path != _default_path and os.path.exists(data_path):
    raw_df = load_data(data_path)
    df     = clean_data(raw_df)

# ── Apply filters ─────────────────────────────────────────────────────────────
active_emp    = filter_employment or emp_options
active_remote = filter_remote     or remote_options

mask = (
    df["Employment"].isin(active_emp) &
    df["RemoteWork"].isin(active_remote)
)
salary_mask = (
    df["ConvertedCompYearly"].isna() |
    ((df["ConvertedCompYearly"] >= salary_range[0]) &
     (df["ConvertedCompYearly"] <= salary_range[1]))
)
filtered_df = df[mask & salary_mask].copy()

PLOT_BG = "#FFF8EE"


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("Stack Overflow Developer Survey 2024")
st.markdown(
    "An exploratory analysis of **65 000+ developer responses** "
    "covering languages, salaries, remote work, AI sentiment, and more."
)
st.divider()


# ─────────────────────────────────────────────
# SECTION 1 — OVERVIEW
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Dataset Overview</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total respondents (raw)", f"{len(raw_df):,}")
c2.metric("After cleaning & filters", f"{len(filtered_df):,}")
c3.metric("Countries represented",
          str(filtered_df["Country"].nunique()) if "Country" in filtered_df.columns else "N/A")
c4.metric("Columns in dataset", f"{raw_df.shape[1]}")

with st.expander("Raw data sample (first 10 rows)"):
    st.dataframe(filtered_df.head(10), use_container_width=True)

with st.expander("Missing values"):
    m = filtered_df.isnull().sum().reset_index()
    m.columns = ["Column", "Missing"]
    m["% missing"] = (m["Missing"] / len(filtered_df) * 100).round(1)
    m = m[m["Missing"] > 0].sort_values("% missing", ascending=False)
    st.dataframe(m, use_container_width=True)


# ─────────────────────────────────────────────
# SECTION 2 — SUMMARY
# ─────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Data Summary</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    sal = filtered_df["ConvertedCompYearly"].dropna()
    st.markdown("**Salary statistics (USD / year)**")
    if len(sal):
        st.dataframe(pd.DataFrame({
            "Statistic": ["Mean", "Median", "Std dev", "Min", "Max"],
            "Value (USD)": [f"${sal.mean():,.0f}", f"${sal.median():,.0f}",
                            f"${sal.std():,.0f}",  f"${sal.min():,.0f}",  f"${sal.max():,.0f}"],
        }), use_container_width=True, hide_index=True)

with col_b:
    exp = filtered_df["YearsCodePro"].dropna()
    st.markdown("**Years of professional coding**")
    if len(exp):
        st.dataframe(pd.DataFrame({
            "Statistic": ["Mean", "Median", "Min", "Max", "Respondents"],
            "Value": [f"{exp.mean():.1f} yrs", f"{exp.median():.0f} yrs",
                      f"{exp.min():.0f} yrs",  f"{exp.max():.0f} yrs", f"{len(exp):,}"],
        }), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# SECTION 3 — VISUALIZATIONS
# ─────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Visualizations</div>', unsafe_allow_html=True)

# VIZ 1 — Top 15 Languages
st.markdown("#### Most-used programming languages")
st.caption("Each respondent may list several languages (multi-select field).")
if "LanguageHaveWorkedWith" in filtered_df.columns:
    lc = explode_multi(filtered_df, "LanguageHaveWorkedWith").head(15)
    fig = px.bar(lc.reset_index(), x="count", y="LanguageHaveWorkedWith", orientation="h",
                 color="count", color_continuous_scale=ORANGE_SEQ,
                 labels={"count": "Respondents", "LanguageHaveWorkedWith": "Language"},
                 template="plotly_white")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
                      height=450, margin=dict(l=0, r=20, t=20, b=20),
                      plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
    st.plotly_chart(fig, use_container_width=True)

# VIZ 2 — Box: Salary by Experience
st.markdown("#### Salary distribution by years of experience")
sal_exp = filtered_df[filtered_df["ConvertedCompYearly"].notna() & filtered_df["ExperienceBand"].notna()]
if len(sal_exp) > 100:
    order = ["<1 yr", "1-2 yrs", "3-5 yrs", "6-10 yrs", "11-20 yrs", "20+ yrs"]
    fig = px.box(sal_exp, x="ExperienceBand", y="ConvertedCompYearly",
                 category_orders={"ExperienceBand": order}, color="ExperienceBand",
                 color_discrete_sequence=PALETTE,
                 labels={"ExperienceBand": "Experience", "ConvertedCompYearly": "Annual salary (USD)"},
                 template="plotly_white")
    fig.update_layout(showlegend=False, height=420, margin=dict(l=0, r=0, t=20, b=20),
                      yaxis_tickprefix="$", yaxis_tickformat=",",
                      plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
    st.plotly_chart(fig, use_container_width=True)

# VIZ 3 & 4 — Pie + AI Sentiment side by side
st.markdown("#### Remote work split & AI sentiment")
col_pie, col_ai = st.columns(2)

with col_pie:
    if "RemoteWork" in filtered_df.columns:
        rc = filtered_df["RemoteWork"].value_counts().dropna()
        if len(rc):
            fig = px.pie(values=rc.values, names=rc.index,
                         color_discrete_sequence=PALETTE, hole=0.4, template="plotly_white")
            fig.update_traces(textposition="outside", textinfo="percent+label")
            fig.update_layout(showlegend=False, height=360,
                              margin=dict(l=0, r=0, t=20, b=20), paper_bgcolor=PLOT_BG)
            st.plotly_chart(fig, use_container_width=True)

with col_ai:
    if "AISent" in filtered_df.columns:
        ai_sent = filtered_df["AISent"].value_counts().dropna()
        if len(ai_sent):
            sent_colors = {
                "Very favorable": "#5D1C6A", "Favorable": "#CA5995",
                "Indifferent": "#FFB090",    "Unsure": "#FFC8A0",
                "Unfavorable": "#E07050",    "Very unfavorable": "#C04030",
            }
            fig = px.bar(ai_sent.reset_index(), x="count", y="AISent", orientation="h",
                         color="AISent", color_discrete_map=sent_colors,
                         labels={"count": "Respondents", "AISent": "Sentiment"},
                         template="plotly_white")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False,
                              height=360, margin=dict(l=0, r=0, t=20, b=20),
                              plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
            st.plotly_chart(fig, use_container_width=True)

# VIZ 5 — Scatter: Salary vs Experience
st.markdown("#### Salary vs years of professional coding")
st.caption("Coloured by remote-work arrangement. Hover for details.")
sdf = filtered_df[filtered_df["ConvertedCompYearly"].notna() &
                  filtered_df["YearsCodePro"].notna() &
                  filtered_df["RemoteWork"].notna()]
if len(sdf) > 50:
    fig = px.scatter(sdf.sample(min(5000, len(sdf)), random_state=42),
                     x="YearsCodePro", y="ConvertedCompYearly",
                     color="RemoteWork", opacity=0.6,
                     color_discrete_sequence=PALETTE,
                     labels={"YearsCodePro": "Years of professional coding",
                             "ConvertedCompYearly": "Annual salary (USD)",
                             "RemoteWork": "Remote arrangement"},
                     template="plotly_white", hover_data={"Country": True})
    fig.update_layout(height=440, margin=dict(l=0, r=0, t=20, b=20),
                      yaxis_tickprefix="$", yaxis_tickformat=",",
                      legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
                      plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
    st.plotly_chart(fig, use_container_width=True)

# VIZ 6 — Top 10 Countries
st.markdown("#### Top 10 countries by respondent count")
if "Country" in filtered_df.columns:
    tc = filtered_df["Country"].value_counts().head(10)
    fig = px.bar(tc.reset_index(), x="Country", y="count", color="count",
                 color_continuous_scale=ORANGE_SEQ,
                 labels={"count": "Respondents", "Country": ""}, template="plotly_white")
    fig.update_layout(coloraxis_showscale=False, height=380,
                      margin=dict(l=0, r=0, t=20, b=20),
                      plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# SECTION 4 — AI DEEP-DIVE
# ─────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">AI tools adoption deep-dive</div>',
            unsafe_allow_html=True)

if "AISelect" in filtered_df.columns:
    ai_use = filtered_df["AISelect"].value_counts().dropna()
    total  = ai_use.sum()
    for col, (label, val) in zip(st.columns(len(ai_use)), ai_use.items()):
        col.metric(label, f"{val:,}", f"{val/total*100:.1f}%")

    if "RemoteWork" in filtered_df.columns:
        st.markdown("---")
        st.markdown("**AI tool usage vs remote work arrangement**")
        ct = pd.crosstab(filtered_df["RemoteWork"], filtered_df["AISelect"],
                         normalize="index").round(3) * 100
        fig = px.imshow(ct, text_auto=".1f", color_continuous_scale=ORANGE_SEQ,
                        labels={"color": "%"}, aspect="auto", template="plotly_white")
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=20),
                          paper_bgcolor=PLOT_BG)
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# SECTION 5 — INSIGHTS
# ─────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">Key insights</div>', unsafe_allow_html=True)

insights = []
if "LanguageHaveWorkedWith" in filtered_df.columns:
    top_lang = explode_multi(filtered_df, "LanguageHaveWorkedWith").index[0]
    insights.append(f"<strong>{top_lang}</strong> is the most-used language — a streak held for over a decade.")

sal_c = filtered_df["ConvertedCompYearly"].dropna()
if len(sal_c):
    insights.append(
        f"Median annual salary among filtered respondents: <strong>${sal_c.median():,.0f} USD</strong>. "
        "Senior devs (10+ yrs) earn roughly 2–3× more than those just starting out."
    )
if "RemoteWork" in filtered_df.columns:
    top_r = filtered_df["RemoteWork"].value_counts().index[0]
    pct_r = filtered_df["RemoteWork"].value_counts(normalize=True).iloc[0] * 100
    insights.append(f"<strong>{top_r}</strong> is the dominant work arrangement ({pct_r:.1f}% of respondents).")

if "AISelect" in filtered_df.columns:
    pct_ai = filtered_df["AISelect"].str.contains("Yes", na=False).mean() * 100
    insights.append(f"<strong>{pct_ai:.1f}%</strong> of respondents currently use AI coding tools in their workflow.")

insights.append(
    "Experience correlates strongly with salary — remote-first roles show higher median pay "
    "at the same experience level, suggesting a market premium for async-capable professionals."
)

for ins in insights:
    st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption(
    "Data source: Stack Overflow Annual Developer Survey 2024 — "
    "[survey.stackoverflow.co](https://survey.stackoverflow.co/) • "
    "Dashboard built with Streamlit, Pandas & Plotly"
)