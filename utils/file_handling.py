import os
import pandas as pd
import streamlit as st

def reset_app_state():
    if os.path.exists("last_baseline.csv"):
        os.remove("last_baseline.csv")
    if os.path.exists("last_actuals.csv"):
        os.remove("last_actuals.csv")
    for key in ["baseline_data", "actuals_data"]:
        st.session_state.pop(key, None)
    st.rerun()

def save_uploaded_baseline(file):
    df = pd.read_csv(file)
    df.to_csv("last_baseline.csv", index=False)
    st.session_state["baseline_data"] = df

def save_uploaded_actuals(files):
    week_to_actuals = {}
    for file in files:
        df = pd.read_csv(file, skiprows=1, names=["Project Full Name", "Actual Hours"])
        df["Week"] = file.name.split("_")[1].split(".")[0]
        week_to_actuals[df["Week"].iloc[0]] = df
    combined = pd.concat(week_to_actuals.values(), ignore_index=True)
    combined.to_csv("last_actuals.csv", index=False)
    st.session_state["actuals_data"] = list(week_to_actuals.values())
