# Reservoir Optimization Formulation

This file summarizes the mathematical formulation used by `reservoir_optimize.py`.

## Decision Variables

For a 7-day drought dispatch horizon, the decision variables are the daily reservoir releases:

```text
Q_t, t = 1, 2, ..., 7
```

where `Q_t` is measured in m3/s.

## Parameters

```text
Initial storage V_0 = 500,000 m3
Minimum storage V_min = 100,000 m3
Maximum storage V_max = 1,000,000 m3
Minimum ecological release Q_eco = 10 m3/s
Maximum release Q_max = 100 m3/s
Inflow forecast I_t = [15, 12, 10, 8, 12, 15, 18] m3/s
Hydropower price p_t = [0.08, 0.08, 0.08, 0.08, 0.10, 0.12, 0.10] USD/kWh
Time step Delta t = 86,400 s
```

## Storage Balance

The reservoir storage is updated by mass balance:

```text
V_{t+1} = V_t + (I_t - Q_t) * Delta t
```

The implementation calculates the complete storage trajectory from the release vector and then validates the residual of this equation for every day.

## Objective

The main operating objective is to maximize hydropower revenue while maintaining ecological releases:

```text
maximize sum(E_t * p_t)
```

where daily generated energy is represented as:

```text
E_t = Q_t * Delta t * hydropower_factor
```

For the trade-off analysis, the code normalizes hydropower revenue and ecological deficit, then solves weighted objective variants to generate a Pareto frontier.

## Constraints

Storage bounds:

```text
V_min <= V_t <= V_max
```

Release bounds:

```text
Q_eco <= Q_t <= Q_max
```

Ecological deficit for soft-constraint trade-off runs:

```text
deficit_t = max(Q_eco - Q_t, 0)
```

## Validation Checks

`validation_report.txt` verifies:

- release bounds
- minimum ecological release
- storage bounds
- mass balance residual
- total revenue calculation

The baseline schedule satisfies all physical constraints.
