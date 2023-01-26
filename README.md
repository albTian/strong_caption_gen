# Strong data to caption parser
A python + streamlit (?) app to generate captions from exported strong data

### Input -> output
Input: raw csv strong data
Output: formatted captions, in the format of:
```
1/17: AT EGO week 1 day 1
Squat: 3x6, 205lbs
DB RDL: 8/7/8/6, 65lbs
Leg press: 2x8, 360lbs | 2x8, 450lbs
Back extension: 2x12
Intensity: 4
```

```
m/dd: AT 'PROGRAM' week 'w' day 'd'
'Exercise 1': 'set'x'reps', 'weight'
'Exercise w diff weights': 'set'x'reps', 'weight' | 'set'x'reps', 'weight'
Intensity: 'i'
```

### Approach
- Start very basic. Function to generate Exercise lines, header line and more
- Parse and group data into workouts
- Per workout:
  - Group by weight
    - if all reps are the same, sets x reps
    - if different, use the 'a/b/c' format
  - 


### Challenges
- 