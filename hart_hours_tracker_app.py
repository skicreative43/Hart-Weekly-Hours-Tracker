import streamlit as st
from utils.file_handling import reset_app_state, save_uploaded_baseline, save_uploaded_actuals
from utils.data_processing import clean_baseline, generate_weekly_columns, distribute_hours, summarize_totals
from utils.visualization import create_weekly_chart, build_recap_html, export_html
import pandas as pd
import datetime
import os

st.set_page_config(layout="wide")

# Sidebar: Reset app
st.sidebar.header("⚙️ Settings")
if st.sidebar.button("🔁 Start Fresh"):
    reset_app_state()

st.title("📈 Hart Weekly Hours Tracker")

# Sidebar: Upload files
st.sidebar.header("📤 Upload New Files")
new_baseline = st.sidebar.file_uploader("Upload New Baseline (.csv)", type=["csv"], key="new_baseline")
new_actuals = st.sidebar.file_uploader("Upload New Actuals (.csv)", type=["csv"], accept_multiple_files=True, key="new_actuals")
update_chart = st.sidebar.button("🔄 Update Chart")

if new_baseline:
    save_uploaded_baseline(new_baseline)
    st.rerun()

if new_actuals and update_chart:
    save_uploaded_actuals(new_actuals)
    st.success("✅ Chart and recap successfully updated!")
    st.stop()

# Load stored data
if "baseline_data" not in st.session_state or "actuals_data" not in st.session_state:
    # Attempt to load from disk if available
    if os.path.exists("last_baseline.csv") and os.path.exists("last_actuals.csv"):
        st.session_state["baseline_data"] = pd.read_csv("last_baseline.csv")
        actuals_df = pd.read_csv("last_actuals.csv")
        if "Week" in actuals_df.columns:
            st.session_state["actuals_data"] = [df for _, df in actuals_df.groupby("Week")]
    else:
        st.info("👋 Please upload a baseline file and at least one actual hours file to get started.")
        baseline_file = st.file_uploader("Upload Baseline File (.csv)", type=["csv"], key="baseline_start")
        actuals_files = st.file_uploader("Upload Actuals Files (.csv)", type=["csv"], accept_multiple_files=True, key="actuals_start")
        if baseline_file and actuals_files:
            save_uploaded_baseline(baseline_file)
            save_uploaded_actuals(actuals_files)
            st.success("Files uploaded. Please rerun the app.")
        st.stop()

# Begin processing
baseline_df = st.session_state["baseline_data"].copy()
actuals_all = pd.concat(st.session_state["actuals_data"], ignore_index=True)

baseline_df = clean_baseline(baseline_df)
baseline_df, week_range = generate_weekly_columns(baseline_df)
baseline_df, skipped_projects = distribute_hours(baseline_df, week_range)
totals_df = summarize_totals(baseline_df, actuals_all, week_range)

# Grand totals and recap
grand_est = round(baseline_df["Current Budget Hours"].sum())
grand_act = round(baseline_df["Actual Hours"].sum(), 2)

today = pd.Timestamp.today().normalize()
import re
weekly_cols = [c for c in baseline_df.columns if re.match(r"\d{4}-\d{2}-\d{2}", c)]
as_of_cols = [c for c in weekly_cols if pd.to_datetime(c) <= today]
as_of_est = round(baseline_df[as_of_cols].sum().sum(), 1) if as_of_cols else 0.0
as_of_act = round(baseline_df["Actual Hours"].sum(), 2)

as_of_pct = round((as_of_act / as_of_est) * 100, 1) if as_of_est > 0 else 0.0

# Plot
fig = create_weekly_chart(totals_df)
st.plotly_chart(fig, use_container_width=True)

# Recap
recap_html = build_recap_html(skipped_projects=skipped_projects, 
    skipped_projects=skipped_projects,
    grand_est=grand_est,
    grand_act=grand_act,
    as_of_est=as_of_est,
    as_of_act=as_of_act,
    as_of_pct=as_of_pct,
    today=today,
    project_df=baseline_df.sort_values("Project Full Name")
)
st.markdown(recap_html, unsafe_allow_html=True)

# Export
html_data = export_html(fig, recap_html)
st.download_button("Download Chart & Recap (HTML)", data=html_data, file_name="weekly_hours_chart.html", mime="text/html")
