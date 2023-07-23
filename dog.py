import streamlit as st

# import numpy as np
import pandas as pd

# import matplotlib.pyplot as plt
import re
import altair as alt


DEFAULT_METRICS = ["Weight", "Reps", "1 Rep Max"]


def one_rep_max(weight: pd.Series, reps: pd.Series):
    return weight / (1.0278 - 0.0278 * reps.clip(0, 10))


def main():
    csv_file = st.file_uploader("Upload a strong export", type=["csv"])
    if not csv_file:
        return

    # Read the table (auto cleans the nan)
    df = pd.read_csv(csv_file, na_filter=False)
    df["Date"] = pd.to_datetime(df["Date"])
    df["1 Rep Max"] = one_rep_max(df["Weight"], df["Reps"])

    # Select exercises
    all_e_names = df["Exercise Name"].unique()
    selected_e_names = st.multiselect("Select exercises", all_e_names)
    pattern = "|".join(map(re.escape, selected_e_names))
    selected_e_df = df[df["Exercise Name"].str.fullmatch(pattern)]

    # Select metric to display
    selected_metric = st.selectbox("Select metric", DEFAULT_METRICS)

    # Full rows, selected for maximum selected_metric
    idx = selected_e_df.groupby(["Date", "Exercise Name"])[selected_metric].idxmax()
    df_maxed = selected_e_df.loc[idx].reset_index(drop=True)

    # Use altair to display
    c = (
        alt.Chart(df_maxed)
        .mark_line()
        .encode(x="Date", y=selected_metric, color="Exercise Name")
    )
    st.altair_chart(c, use_container_width=True)


main()
