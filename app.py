import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="HR Analytics Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #5DADE2;
        margin-bottom: 8px;
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
    .metric-label { font-size: 13px; color: #666; margin-top: 2px; }
    .section-header {
        font-size: 18px; font-weight: 600;
        color: #1a1a2e; margin: 20px 0 10px;
        border-bottom: 2px solid #f0f0f0; padding-bottom: 6px;
    }
    .sql-box {
        background: #1e1e2e; color: #cdd6f4;
        border-radius: 8px; padding: 14px;
        font-family: monospace; font-size: 13px;
        line-height: 1.6; margin: 8px 0;
    }
    .insight-box {
        background: #fff8e7; border-left: 4px solid #FAD7A0;
        border-radius: 8px; padding: 12px 16px; margin: 8px 0;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


# ── DATABASE SETUP ────────────────────────────────────────────
@st.cache_resource
def get_connection():
    np.random.seed(42)
    n = 1000
    departments = ["Engineering", "Sales", "HR", "Marketing", "Finance", "Operations"]
    job_levels  = ["Junior", "Mid", "Senior", "Lead", "Manager"]
    genders     = ["Male", "Female"]
    education   = ["Bachelor", "Master", "PhD", "High School"]

    df = pd.DataFrame({
        "employee_id"  : range(1001, 1001 + n),
        "department"   : np.random.choice(departments, n, p=[0.30, 0.20, 0.10, 0.15, 0.10, 0.15]),
        "job_level"    : np.random.choice(job_levels,  n, p=[0.25, 0.30, 0.25, 0.12, 0.08]),
        "gender"       : np.random.choice(genders,     n, p=[0.55, 0.45]),
        "education"    : np.random.choice(education,   n, p=[0.50, 0.30, 0.10, 0.10]),
        "age"          : np.random.randint(22, 60, n),
        "tenure_years" : np.random.randint(0, 20, n),
        "salary"       : np.random.randint(35000, 150000, n),
        "performance"  : np.random.choice([1,2,3,4,5], n, p=[0.05, 0.10, 0.35, 0.35, 0.15]),
        "satisfaction" : np.random.choice([1,2,3,4,5], n, p=[0.08, 0.12, 0.30, 0.35, 0.15]),
        "overtime"     : np.random.choice([0, 1], n, p=[0.65, 0.35]),
        "attrition"    : np.random.choice([0, 1], n, p=[0.84, 0.16]),
        "hire_year"    : np.random.randint(2005, 2024, n),
        "last_promotion": np.random.randint(0, 6, n),
        "training_hours": np.random.randint(0, 80, n),
    })
    level_mult = {"Junior": 0.6, "Mid": 0.85, "Senior": 1.1, "Lead": 1.35, "Manager": 1.6}
    df["salary"] = df.apply(
        lambda r: int(r["salary"] * level_mult[r["job_level"]]), axis=1
    ).clip(28000, 200000)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("employees", conn, if_exists="replace", index=False)
    return conn

conn = get_connection()

def query(sql):
    return pd.read_sql_query(sql, conn)


# ── SIDEBAR FILTERS ───────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/conference-call.png", width=60)
st.sidebar.title("HR Analytics")
st.sidebar.markdown("---")

all_depts = query("SELECT DISTINCT department FROM employees ORDER BY department")["department"].tolist()
sel_depts = st.sidebar.multiselect("Department", all_depts, default=all_depts)

all_levels = ["Junior", "Mid", "Senior", "Lead", "Manager"]
sel_levels = st.sidebar.multiselect("Job Level", all_levels, default=all_levels)

sel_gender = st.sidebar.multiselect("Gender", ["Male", "Female"], default=["Male", "Female"])

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown(
    "SQL-powered HR dashboard built with **SQLite + Streamlit**.\n\n"
    "All queries run live against an in-memory database."
)

# Build filter clause
dept_str  = ", ".join(f"'{d}'" for d in sel_depts)  or "''"
level_str = ", ".join(f"'{l}'" for l in sel_levels) or "''"
gen_str   = ", ".join(f"'{g}'" for g in sel_gender) or "''"
filt = f"WHERE department IN ({dept_str}) AND job_level IN ({level_str}) AND gender IN ({gen_str})"


# ── MAIN TITLE ────────────────────────────────────────────────
st.title("👥 HR Analytics Dashboard")
st.caption("Live SQL queries · 1,000 employee records · SQLite in-memory database")

# ── KPI ROW ───────────────────────────────────────────────────
kpis = query(f"""
    SELECT
        COUNT(*)                                         AS total,
        SUM(attrition)                                   AS left_co,
        ROUND(SUM(attrition)*100.0/COUNT(*),1)           AS attr_rate,
        ROUND(AVG(salary),0)                             AS avg_sal,
        ROUND(AVG(satisfaction),2)                       AS avg_sat,
        ROUND(AVG(performance),2)                        AS avg_perf
    FROM employees {filt}
""").iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Employees",   f"{int(kpis['total']):,}")
c2.metric("Attrition Rate",    f"{kpis['attr_rate']}%")
c3.metric("Avg Salary",        f"${int(kpis['avg_sal']):,}")
c4.metric("Avg Satisfaction",  f"{kpis['avg_sat']} / 5")
c5.metric("Avg Performance",   f"{kpis['avg_perf']} / 5")

st.markdown("---")

# ── TABS ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Attrition", "💰 Compensation", "📈 Workforce", "🚨 At-Risk", "🔍 SQL Explorer"
])


# ════════════════════════════════════════════════════
# TAB 1 — ATTRITION
# ════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Attrition Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        q_attr = query(f"""
            SELECT department,
                   COUNT(*) AS total,
                   ROUND(SUM(attrition)*100.0/COUNT(*),1) AS attrition_pct
            FROM employees {filt}
            GROUP BY department ORDER BY attrition_pct DESC
        """)
        fig, ax = plt.subplots(figsize=(6, 4))
        colors = ["#F1948A","#FAD7A0","#AED6F1","#A9DFBF","#D2B4DE","#FADADD"]
        ax.barh(q_attr["department"], q_attr["attrition_pct"],
                color=colors[:len(q_attr)], edgecolor="none")
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_title("Attrition Rate by Department", fontweight="bold")
        ax.invert_yaxis()
        for i, v in enumerate(q_attr["attrition_pct"]):
            ax.text(v + 0.2, i, f"{v}%", va="center", fontsize=9)
        sns.despine()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        q_ot = query(f"""
            SELECT CASE WHEN overtime=1 THEN 'Overtime' ELSE 'No Overtime' END AS ot,
                   ROUND(SUM(attrition)*100.0/COUNT(*),1) AS attrition_pct
            FROM employees {filt} GROUP BY overtime
        """)
        q_ten = query(f"""
            SELECT CASE
                WHEN tenure_years BETWEEN 0 AND 2  THEN '0-2 yrs'
                WHEN tenure_years BETWEEN 3 AND 5  THEN '3-5 yrs'
                WHEN tenure_years BETWEEN 6 AND 10 THEN '6-10 yrs'
                ELSE '10+ yrs' END AS bucket,
                ROUND(SUM(attrition)*100.0/COUNT(*),1) AS attrition_pct
            FROM employees {filt}
            GROUP BY bucket ORDER BY MIN(tenure_years)
        """)
        fig, axes = plt.subplots(1, 2, figsize=(6, 4))
        axes[0].bar(q_ot["ot"], q_ot["attrition_pct"],
                    color=["#F1948A","#AED6F1"], edgecolor="none", width=0.4)
        axes[0].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        axes[0].set_title("Overtime vs Attrition", fontweight="bold", fontsize=10)
        sns.despine(ax=axes[0])

        axes[1].bar(q_ten["bucket"], q_ten["attrition_pct"],
                    color=["#F1948A","#FAD7A0","#A9DFBF","#AED6F1"],
                    edgecolor="none", width=0.5)
        axes[1].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        axes[1].set_title("Attrition by Tenure", fontweight="bold", fontsize=10)
        axes[1].tick_params(axis="x", labelsize=8)
        sns.despine(ax=axes[1])

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.markdown('<div class="insight-box">💡 <b>Insight:</b> Employees who work overtime leave at significantly higher rates. Early tenure (0–2 years) also shows the highest attrition — onboarding and early engagement are critical.</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# TAB 2 — COMPENSATION
# ════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Compensation Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        q_sal = query(f"""
            SELECT job_level, gender, ROUND(AVG(salary),0) AS avg_salary
            FROM employees {filt}
            GROUP BY job_level, gender
        """)
        pivot = q_sal.pivot(index="job_level", columns="gender", values="avg_salary")
        pivot = pivot.reindex(["Junior","Mid","Senior","Lead","Manager"])
        fig, ax = plt.subplots(figsize=(6, 4))
        pivot.plot(kind="bar", ax=ax, color=["#AED6F1","#F1948A"],
                   edgecolor="none", width=0.6)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))
        ax.set_title("Avg Salary by Level & Gender", fontweight="bold")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=0)
        ax.legend(title="Gender")
        sns.despine()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        q_gap = query(f"""
            SELECT department,
                ROUND(AVG(CASE WHEN gender='Male'   THEN salary END),0) AS male_sal,
                ROUND(AVG(CASE WHEN gender='Female' THEN salary END),0) AS female_sal,
                ROUND((AVG(CASE WHEN gender='Male' THEN salary END) -
                       AVG(CASE WHEN gender='Female' THEN salary END))
                      *100.0/AVG(CASE WHEN gender='Male' THEN salary END),1) AS gap_pct
            FROM employees {filt} GROUP BY department ORDER BY gap_pct DESC
        """)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.barh(q_gap["department"], q_gap["gap_pct"],
                color=["#F1948A" if x > 0 else "#AED6F1" for x in q_gap["gap_pct"]],
                edgecolor="none")
        ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
        ax.set_title("Gender Pay Gap % by Department", fontweight="bold")
        sns.despine()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.dataframe(q_gap.style.format({"male_sal": "${:,.0f}", "female_sal": "${:,.0f}", "gap_pct": "{:.1f}%"}),
                 use_container_width=True)


# ════════════════════════════════════════════════════
# TAB 3 — WORKFORCE
# ════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Workforce Trends</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        q_hire = query(f"""
            SELECT hire_year, COUNT(*) AS new_hires
            FROM employees {filt}
            GROUP BY hire_year ORDER BY hire_year
        """)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(q_hire["hire_year"], q_hire["new_hires"],
                color="#5DADE2", linewidth=2.5, marker="o", markersize=5)
        ax.fill_between(q_hire["hire_year"], q_hire["new_hires"], alpha=0.12, color="#5DADE2")
        ax.set_title("Yearly Hiring Trend", fontweight="bold")
        ax.set_xlabel("Year")
        sns.despine()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        q_train = query(f"""
            SELECT performance, ROUND(AVG(training_hours),1) AS avg_hours
            FROM employees {filt}
            GROUP BY performance ORDER BY performance
        """)
        fig, ax = plt.subplots(figsize=(6, 4))
        colors_perf = ["#F1948A","#FAD7A0","#AED6F1","#A9DFBF","#82E0AA"]
        ax.bar(q_train["performance"].astype(str), q_train["avg_hours"],
               color=colors_perf, edgecolor="none", width=0.5)
        ax.set_title("Avg Training Hours by Performance", fontweight="bold")
        ax.set_xlabel("Performance Score (1=Low, 5=High)")
        ax.set_ylabel("Avg Training Hours")
        sns.despine()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    q_dept_full = query(f"""
        SELECT department,
               COUNT(*) AS headcount,
               ROUND(AVG(satisfaction),2) AS avg_satisfaction,
               ROUND(AVG(performance),2)  AS avg_performance,
               ROUND(AVG(salary),0)       AS avg_salary
        FROM employees {filt}
        GROUP BY department ORDER BY headcount DESC
    """)
    st.dataframe(q_dept_full.style.format({
        "avg_salary": "${:,.0f}", "avg_satisfaction": "{:.2f}", "avg_performance": "{:.2f}"
    }), use_container_width=True)


# ════════════════════════════════════════════════════
# TAB 4 — AT-RISK EMPLOYEES
# ════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">High Performers at Risk</div>', unsafe_allow_html=True)
    st.markdown("Employees with **performance ≥ 4** and **satisfaction ≤ 2** who haven't left yet — these are your retention priorities.")

    perf_min = st.slider("Min Performance Score", 1, 5, 4)
    sat_max  = st.slider("Max Satisfaction Score", 1, 5, 2)

    q_risk = query(f"""
        SELECT employee_id, department, job_level, gender,
               salary, performance, satisfaction, tenure_years, training_hours
        FROM employees
        {filt.replace('WHERE', 'WHERE')} AND department IN ({dept_str})
          AND performance >= {perf_min}
          AND satisfaction <= {sat_max}
          AND attrition = 0
        ORDER BY performance DESC, satisfaction ASC
    """)

    st.metric("Employees at Risk", len(q_risk))

    if len(q_risk) > 0:
        st.dataframe(
            q_risk.style
            .format({"salary": "${:,.0f}"})
            .background_gradient(subset=["performance"], cmap="Greens")
            .background_gradient(subset=["satisfaction"], cmap="Reds_r"),
            use_container_width=True
        )
        st.markdown('<div class="insight-box">🚨 <b>Action needed:</b> Schedule 1-on-1 retention conversations with these employees immediately. Focus on career growth, workload, and compensation review.</div>', unsafe_allow_html=True)
    else:
        st.success("No at-risk employees found with current filters!")


# ════════════════════════════════════════════════════
# TAB 5 — SQL EXPLORER
# ════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Live SQL Explorer</div>', unsafe_allow_html=True)
    st.markdown("Write and run any SQL query directly against the `employees` table.")

    st.markdown("**Available columns:** `employee_id, department, job_level, gender, education, age, tenure_years, salary, performance, satisfaction, overtime, attrition, hire_year, last_promotion, training_hours`")

    example_queries = {
        "Attrition by department"       : "SELECT department, COUNT(*) AS total,\n  ROUND(SUM(attrition)*100.0/COUNT(*),1) AS attrition_pct\nFROM employees\nGROUP BY department\nORDER BY attrition_pct DESC",
        "Top 5 earners per department"  : "SELECT department, employee_id, job_level, salary\nFROM (\n  SELECT *, RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS rnk\n  FROM employees\n)\nWHERE rnk <= 5\nORDER BY department, salary DESC",
        "Gender pay gap"                : "SELECT department,\n  ROUND(AVG(CASE WHEN gender='Male' THEN salary END),0) AS male_sal,\n  ROUND(AVG(CASE WHEN gender='Female' THEN salary END),0) AS female_sal\nFROM employees\nGROUP BY department",
        "Custom query"                  : "SELECT * FROM employees LIMIT 10",
    }

    selected = st.selectbox("Load an example query", list(example_queries.keys()))
    sql_input = st.text_area("SQL Query", value=example_queries[selected], height=160)

    if st.button("▶ Run Query", type="primary"):
        try:
            result = query(sql_input)
            st.success(f"Returned {len(result)} rows")
            st.dataframe(result, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Error: {e}")

    st.markdown("---")
    st.markdown("**Database Schema**")
    st.code("""
CREATE TABLE employees (
    employee_id    INTEGER,
    department     TEXT,
    job_level      TEXT,
    gender         TEXT,
    education      TEXT,
    age            INTEGER,
    tenure_years   INTEGER,
    salary         INTEGER,
    performance    INTEGER,   -- 1 (low) to 5 (high)
    satisfaction   INTEGER,   -- 1 (low) to 5 (high)
    overtime       INTEGER,   -- 0 or 1
    attrition      INTEGER,   -- 0 = stayed, 1 = left
    hire_year      INTEGER,
    last_promotion INTEGER,   -- years since last promotion
    training_hours INTEGER
)
    """, language="sql")
