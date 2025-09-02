import pandas as pd

def clean_baseline(df):
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        df.columns[0]: "Project Full Name",
        df.columns[1]: "Project Start Date",
        df.columns[2]: "Project Due Date",
        df.columns[3]: "Current Budget Hours",
        df.columns[4]: "Actual Hours",
        df.columns[5]: "Remaining"
    })
    df["Project Start Date"] = pd.to_datetime(df["Project Start Date"], errors='coerce')
    df["Project Due Date"] = pd.to_datetime(df["Project Due Date"], errors='coerce')
    df["Current Budget Hours"] = pd.to_numeric(df["Current Budget Hours"], errors='coerce')
    df["Actual Hours"] = pd.to_numeric(df["Actual Hours"], errors='coerce')
    df["Remaining"] = (df["Current Budget Hours"] - df["Actual Hours"]).round(1)
    return df

def generate_weekly_columns(df):
    min_start = df["Project Start Date"].min()
    max_due = df["Project Due Date"].max()
    week_range = pd.date_range(start=min_start, end=max_due, freq='W-MON')
    if pd.Timestamp('2025-06-30') not in week_range:
        week_range = week_range.insert(0, pd.Timestamp('2025-06-30'))
    for week in week_range:
        df[week.strftime("%Y-%m-%d")] = 0.0
    return df, week_range


import streamlit as st

def distribute_hours(df, week_range):
    skipped_projects = []
    for i, row in df.iterrows():
        start_date = row["Project Start Date"]
        end_date = row["Project Due Date"]

        if pd.isna(start_date) or pd.isna(end_date):
            skipped_projects.append(row["Project Full Name"])
            continue

        weeks = pd.date_range(start=start_date, end=end_date, freq='W-MON')
        per_week = round(row["Remaining"] / len(weeks), 1) if len(weeks) > 0 else 0

        for w in weeks:
            col = w.strftime("%Y-%m-%d")
            if col in df.columns:
                df.at[i, col] = per_week

    if skipped_projects:
        st.warning(f"⚠️ Skipped {len(skipped_projects)} projects due to missing start or end dates.")
        for proj in skipped_projects:
            st.text(f"  - {proj}")

    return df
def summarize_totals(df, actuals, week_range):
    actuals["Actual Hours"] = pd.to_numeric(actuals["Actual Hours"], errors='coerce')
    actuals_sum = actuals.groupby("Week")["Actual Hours"].sum()
    totals = []
    for week in week_range:
        col = week.strftime("%Y-%m-%d")
        totals.append({
            "Week": week,
            "Estimated Hours": round(df[col].sum(), 1),
            "Actual Hours": round(actuals_sum.get(col, 0.0), 1)
        })
    totals_df = pd.DataFrame(totals)
    totals_df["Difference"] = (totals_df["Actual Hours"] - totals_df["Estimated Hours"]).round(1)
    return totals_df