import streamlit as st

# import numpy as np
import pandas as pd

# import matplotlib.pyplot as plt
import re
import altair as alt

from altair import datum


DEFAULT_METRICS = ["Weight", "Reps", "1 Rep Max"]


def one_rep_max(weight: pd.Series, reps: pd.Series):
    return weight / (1.0278 - 0.0278 * reps.clip(0, 10))


TEMP_CSV = "temp.csv"


def correlate_auxiliary_exercises(df, main_lift):
    # Filter sessions where main lift was performed
    main_lift_sessions = df[df["Exercise Name"] == main_lift]

    # Calculate improvement in 1RM for each session
    main_lift_sessions["1RM Improvement"] = main_lift_sessions["1 Rep Max"].diff()

    # Merge with original df to get auxiliary exercises for each session
    aux_lift_sessions = pd.merge(
        df, main_lift_sessions[["Date", "1RM Improvement"]], on="Date"
    )

    # Create correlation matrix
    correlation_df = aux_lift_sessions.groupby("Exercise Name")["1RM Improvement"].corr(
        aux_lift_sessions["1 Rep Max"]
    )

    # Return DataFrame sorted by correlation
    return correlation_df.sort_values(ascending=False)


def calculate_improvements(df, main_lift, period=7):
    # Filter sessions where main lift was performed
    main_lift_sessions = df[df["Exercise Name"] == main_lift]

    # Calculate improvement in 1RM for each session
    main_lift_sessions["1RM Improvement"] = main_lift_sessions["1 Rep Max"].diff()

    # Calculate moving average of improvement
    main_lift_sessions["Moving Average Improvement"] = (
        main_lift_sessions["1RM Improvement"].rolling(window=period).mean()
    )

    # Set the date as the index (important for slicing)
    main_lift_sessions.set_index("Date", inplace=True)

    return main_lift_sessions


def find_max_periods(df, column):
    # Find the date of max improvement and max regression
    max_improvement_start = df[column].idxmax()
    max_regression_start = df[column].idxmin()

    return max_improvement_start.to_pydatetime(), max_regression_start.to_pydatetime()


def main():
    st.write("# Analyze your strong data!")
    # Input csv
    csv_file = st.file_uploader("Upload a strong export", type=["csv"])
    text_input = st.text_area("Paste strong export")
    if text_input:
        with open(TEMP_CSV, "w") as out:
            out.write(text_input)
    if not (csv_file or text_input):
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

    main_lift = st.selectbox("Select main lift", all_e_names)

    correlation_df = correlate_auxiliary_exercises(df, main_lift)

    # Display auxiliary exercise correlations
    st.write(correlation_df)
    # Calculate improvements
    main_lift_sessions = calculate_improvements(df, main_lift)

    # Find periods of max improvement and regression
    max_improvement_start, max_regression_start = find_max_periods(
        main_lift_sessions, "Moving Average Improvement"
    )

    # Create subsets for the periods of max improvement and regression
    improvement_period = main_lift_sessions.loc[
        max_improvement_start : max_improvement_start + pd.Timedelta(days=7)
    ]
    regression_period = main_lift_sessions.loc[
        max_regression_start : max_regression_start + pd.Timedelta(days=7)
    ]

    # Create a chart for the moving average improvement
    c = (
        alt.Chart(main_lift_sessions.reset_index())
        .mark_line()
        .encode(x="Date:T", y="Moving Average Improvement:Q")
    )

    # Highlight periods of max improvement and regression
    highlight = (
        alt.Chart(improvement_period.reset_index())
        .mark_area(color="lightgreen", opacity=0.5)
        .encode(x="Date:T", y="Moving Average Improvement:Q")
    )

    highlight2 = (
        alt.Chart(regression_period.reset_index())
        .mark_area(color="red", opacity=0.5)
        .encode(x="Date:T", y="Moving Average Improvement:Q")
    )

    # Combine the charts
    st.altair_chart(c + highlight + highlight2, use_container_width=True)


main()
