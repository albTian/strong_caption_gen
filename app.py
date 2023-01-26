import streamlit as st
import pandas as pd

# defaults
TEMP_CSV = 'temp.csv'


# For List[Weight] and List[List[Reps]], generate a line
# s["Reps list"] = [[a, b], [c, d]]
# s["Weight"] = [x, y]
def generateLineFromSeries(s):
    name, repsList, weights = s["Exercise Name"], s["Reps"], s["Weight"]
    if name == "Intensity":
        return f"Intensity: {repsList[0][0]}"

    blocks = []
    for weight, reps in zip(weights, repsList):
        # Round to the nearest .5 (for floating point errors) and eliminate trailing .0
        weightStr = str(round(weight * 2) / 2).replace('.0', '')
        weightTag = f', {weightStr}lbs' if weight else ''
        block = ''
        # Amrap rule: 4x4 -> 8 instead of 4/4/4/4/8
        if len(set(reps)) == 2 and len(set(reps[:-1])) == 1:
            block = f'{len(reps)-1}x{reps[0]} -> {reps[-1]}{weightTag}'

        # When we have 1 rep count for all sets
        elif len(set(reps)) == 1:
            block = f'{len(reps)}x{reps[0]}{weightTag}'
        else:
            repStr = '/'.join([str(rep) for rep in reps])
            block = f'{repStr}{weightTag}'

        blocks.append(block)

    meat = " | ".join(blocks)
    return f'{name}: {meat}'


def generateCaption(s, user_name, program_name):
    date, exerciseLine = s["Date parsed"], s["Exercise line"]
    # Use global vars, get assigned during usage
    header = f"{date}: {user_name}{f' {program_name}' if program_name else ''} week X day X"
    return "\n".join([header, exerciseLine])


def displayCaption(s):
    caption = s["Caption"]
    st.write(
        f'''
        ```
        {caption}
        '''
    )


def main():
    st.write("### Either upload or paste strong data")
    # Input csv
    csv_file = st.file_uploader("Upload a strong export", type=["csv"])
    text_input = st.text_area("Paste strong export")
    if text_input:
        with open(TEMP_CSV, 'w') as out:
            out.write(text_input)
    if not (csv_file or text_input):
        return

    # Input options
    num_caps = st.slider("How many captions", min_value=0,max_value=20, value=6)
    user_name = st.selectbox("Whos caption", ["AT", "JQ", "AJ", "DMA"])
    preset_program = st.selectbox("Which program", ["EGO", "JOJO", "JAW", None])
    custom_program = st.text_input("Or enter a custom program")
    program_name = custom_program if custom_program else preset_program

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
        df["Exercise Name"] = df["Exercise Name"].str.replace(" \(Barbell\)", "")
        df["Exercise Name"] = df["Exercise Name"].str.replace(" \(Dumbbell\)", "")
        df["Exercise Name"] = df["Exercise Name"].str.replace(" \(Machine\)", "")

        # Generate per exercise caption lines
        df["Exercise line"] = df.apply(generateLineFromSeries, axis=1)

        # Generate per DATE caption lines (joins with newlines)
        df = df.groupby(["Date"])["Exercise line"].apply(lambda l: '\n'.join(l)).reset_index()
        df["Date parsed"] = df["Date"].dt.strftime("-%m/-%d").str.replace("-0", "-").str.replace("-", "")
        df["Caption"] = df.apply(lambda s: generateCaption(s, user_name, program_name), axis=1)

        # Display to output
        df = df.sort_values("Date", ascending=False)
        df.head(num_caps).apply(displayCaption, axis=1)


main()
