import streamlit as st
import pandas as pd

# defaults
TEMP_CSV = 'temp.csv'


# For List[Weight] and List[List[Reps]], generate a line
# s["Reps list"] = [[a, b], [c, d]] 
# s["Weight"] = [x, y]
def generateCaptionLine(s):
    name, repsList, weights, unit = s["Exercise Name"], s["Reps"], s["Weight"], s["Unit"]
    if name == "Intensity":
        return f"Intensity: {repsList[0][0]}"

    blocks = []
    for weight, reps in zip(weights, repsList):
        # Round to the nearest .5 (for floating point errors) and eliminate trailing .0
        weightStr = str(round(weight * 2) / 2).replace('.0', '')
        # NOW WE GOT KILO PLATES MF YAAAA
        weightTag = f', {weightStr}{unit}' if weight else ''
        block = ''
        # Amrap rule: 4x4 -> 8 instead of 4/4/4/4/8. Avoids 1x5 -> 6 format; will be 5/6 instead
        if len(reps) > 2 and len(set(reps)) == 2 and len(set(reps[:-1])) == 1:
            block = f'{len(reps)-1}x{reps[0]} -> {reps[-1]}{weightTag}'

        # When we have 1 rep count for all sets. 3x12 format
        elif len(set(reps)) == 1:
            block = f'{len(reps)}x{reps[0]}{weightTag}'

        # Varrying rep counts through the sets. 8/8/7/5 format
        else:
            repStr = '/'.join([str(rep) for rep in reps])
            block = f'{repStr}{weightTag}'

        blocks.append(block)

    meat = " | ".join(blocks)
    return f'{name}: {meat}'


# Will change day_week_dict with each iteration
# tbh not the smartest approach but hey monke code
def generateCaption(s, user_name, program_name, day_week_dict):
    date, exerciseLine = s["Date parsed"], s["Exercise line"]
    header = f"{date}: {user_name}"
    if program_name:
        header +=  f" {program_name}"
    if day_week_dict and day_week_dict["week"] > 0:
        week, day, days_per_week = day_week_dict["week"], day_week_dict["day"], day_week_dict["days_per_week"]
        header += f" week {week} day {day}"
        # Decrement week and day
        day_week_dict["week"] -= 1 if day == 1 else 0
        day_week_dict["day"] = day - 1 if day != 1 else days_per_week
    return "\n".join([header, exerciseLine])


def displayCaption(s):
    st.write(
        f'''
        ```
        {s}
        '''
    )


def main():
    st.write("### Either upload or paste strong data brehhh cnme o n")
    # Input csv
    csv_file = st.file_uploader("Upload a strong export", type=["csv"])
    text_input = st.text_area("Paste strong export")
    if text_input:
        with open(TEMP_CSV, 'w') as out:
            out.write(text_input)
    if not (csv_file or text_input):
        return

    # Input options
    user_name = st.selectbox("Whos caption", ["AT", "JQ", "AJ", "DMA"])
    preset_program = st.selectbox("Which program", ["EGO", "JOJO", "JAW", None])
    custom_program = st.text_input("Or enter a custom program")
    program_name = custom_program if custom_program else preset_program

    # Which week + day was the most recent workout? How many days per week?
    st.write("### Week + day of most recent workout")
    st.write("To create `week X day X` tag")
    omit = st.checkbox("Omit the tag")
    day_week_dict = None
    if not omit:
        days_per_week = st.number_input("Days per week", value=6, step=1)
        week = st.number_input("Week #", value=1, step=1, min_value=0)
        day = st.number_input("Day #", value=1, step=1, min_value=0)
        day_week_dict = {
            "day": day,
            "week": week,
            "days_per_week": days_per_week,
        }

    if not user_name:
        return

    with st.spinner("Loading..."): 
        # Start parsing
        csv_to_open = csv_file if csv_file else TEMP_CSV
        df = pd.read_csv(csv_to_open, na_filter=False)
        df["Date"] = pd.to_datetime(df["Date"])

        # Group by Date, Exercise and Weight. Can agg reps using .apply. sort=False to preserve exercise order
        df = df.groupby(["Date", "Exercise Name", "Weight"], sort=False)["Reps"].agg(list).reset_index()
        df = df.groupby(["Date", "Exercise Name"],sort=False).agg(list).reset_index()

        # Exercise name cleanup
        # TODO: Add nicknames for exercises
        df["Exercise Name"] = df["Exercise Name"].str.replace(" \(Barbell\)", "")
        df["Exercise Name"] = df["Exercise Name"].str.replace(" \(Dumbbell\)", "")
        df["Exercise Name"] = df["Exercise Name"].str.replace(" \(Machine\)", "")

        # Need to do unit changing here... 
        num_caps = st.slider("How many captions", min_value=0,max_value=40, value=6)
        # Calculate how many rows were in the last num_caps workouts 
        unique_dates = df['Date'].unique()[::-1]
        last_workouts_dates = unique_dates[:num_caps]
        num_rows = df[df['Date'].isin(last_workouts_dates)].shape[0]

        df = df.tail(num_rows)

        # Generate per exercise caption lines 
        df['Unit'] = 'lbs'      # default lbs
        df = st.data_editor(df)
        df["Exercise line"] = df.apply(generateCaptionLine, axis=1)

        # Generate per DATE caption lines (joins with newlines)
        df = df.groupby(["Date"])["Exercise line"].apply(lambda l: '\n'.join(l)).reset_index()
        df["Date parsed"] = df["Date"].dt.strftime("-%m/-%d").str.replace("-0", "-").str.replace("-", "")
        df["Caption"] = df.apply(lambda s: generateCaption(s, user_name, program_name, day_week_dict), axis=1)
        df = df.sort_values("Date", ascending=False)



        # Display to output
        captions = df["Caption"]
        displayTogether = st.checkbox("Display together")
        if displayTogether:
            combined = captions.str.cat(sep="\n\n")
            displayCaption(combined)
        else:
            captions.apply(displayCaption)


main()
