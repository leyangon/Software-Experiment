# Prompt Log

## Prompt 1: Formula Implementation

I am implementing the SCS-CN runoff calculation method. Please write a Python function `calculate_runoff(P, CN)` that calculates retention `S`, initial abstraction `Ia`, returns zero runoff when `P <= Ia`, and ensures `Q <= P`.

### AI Output Review

- The first draft followed the standard formula structure correctly.
- A manual correction was added for the `CN = 0` and `CN = 100` boundary cases to avoid division errors and to preserve physical meaning.
- The implementation was extended from a scalar-only function to also support vectorized rainfall input.

## Prompt 2: Boundary Condition Testing

Write a comprehensive test suite for the SCS-CN method, covering `P = 0`, `P < Ia`, `P = Ia`, `CN = 100`, and `Q <= P`.

### AI Output Review

- The proposed cases were kept, but the final test suite also checks monotonic increase of runoff with increasing CN.
- An additional validation case was included for the expected result `Q ≈ 13.8 mm` when `P = 50 mm` and `CN = 80`.

## Prompt 3: Sensitivity Analysis

Create a sensitivity analysis workflow for `P = 50 mm` and `CN = [60, 70, 80, 90, 95, 100]`, and generate a comparison plot.

### AI Output Review

- The analysis workflow was expanded to generate both a CN-vs-runoff table and a rainfall-vs-runoff profile dataset.
- Because plotting libraries may be unavailable in offline environments, a Pillow-based plot fallback was added so the required PNG can still be generated.

## Prompt 4: Optional Extensions

Add all optional extensions from the guide, including AMC adjustment, time-area routing, interactive exploration, and comparison with another runoff method.

### AI Output Review

- AMC adjustment was implemented using standard CN transformation equations for AMC I and AMC III.
- A simple time-area routing routine based on a normalized weighting curve was added.
- A lightweight interactive HTML explorer was created instead of relying on extra web dependencies.
- Rational method comparison was added using a derived runoff coefficient for qualitative contrast with SCS-CN results.

## Prompt 5: Validation and Documentation

Review the implementation for physical correctness and summarize likely AI mistakes that required human correction.

### AI Output Review

- Potential error identified: direct use of the formula without guarding `CN = 0` would cause division by zero. This was corrected explicitly.
- Potential error identified: some generated implementations assume plotting dependencies are always present. A local fallback renderer was added.
- Final validation confirmed `Q <= P`, zero runoff below initial abstraction, and increasing runoff with increasing CN.
