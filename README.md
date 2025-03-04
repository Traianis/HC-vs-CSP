# HC vs CSP: A Comparative Analysis

This project compares two constraint satisfaction approaches for generating optimal timetables: **Constraint Satisfaction Problem (CSP)** and **Hill Climbing (HC)**. The goal is to assign courses to available time slots while minimizing conflicts and ensuring fairness in professor schedules.

## Table of Contents
- [Introduction](#introduction)
- [Methodology](#methodology)
- [Implementation](#implementation)
- [Results](#results)
  - [Quantitative Results](#quantitative-results)
  - [Qualitative Results](#qualitative-results)
- [Conclusions](#conclusions)
- [Usage](#usage)

## Introduction
Scheduling university courses while considering room capacities, professor availability, and student needs is a challenging problem. This project implements and compares two approaches:
- **CSP (Constraint Satisfaction Problem):** A systematic approach that guarantees an optimal solution but can be computationally expensive.
- **Hill Climbing (HC):** A heuristic-based search that quickly finds a good (but not necessarily optimal) solution.

## Methodology
We evaluate both methods based on:
1. **Correctness:** Whether the produced timetable is valid.
2. **Execution time:** How quickly a solution is found.
3. **Memory consumption:** How much memory each approach uses.
4. **Soft constraint violations:** Number of minor constraints violated.

## Implementation
### CSP
- Defines variables for courses, professors, and available time slots.
- Uses forward checking and constraint propagation to ensure valid assignments.
- Iteratively assigns values while minimizing conflicts.

### Hill Climbing
- Starts with a randomly generated timetable.
- Uses local search strategies to iteratively improve the schedule.
- Implements random restarts to escape local optima.

## Results
### Quantitative Results
#### Hill Climbing Performance
| Input File            | Average Iterations | Total States Explored | Accepted Cost |
|-----------------------|--------------------|-----------------------|---------------|
| orar_mic_exact       | 1007               | 23,423                | 1             |
| orar_mediu_relaxat   | 87                 | 4,472                 | 1             |
| orar_mare_relaxat    | 243                | 14,641                | 4             |

#### CSP Performance
| Input File            | Best Found Cost | Iterations | States Explored |
|-----------------------|----------------|------------|-----------------|
| orar_mic_exact       | 0              | 38         | 38              |
| orar_mediu_relaxat   | 0              | 64         | 64              |
| orar_mare_relaxat    | 0              | 114        | 114             |

### Key Observations
- **CSP guarantees a conflict-free solution (best cost = 0) with fewer iterations and states explored compared to HC.**
- **HC can explore significantly more states, making it computationally heavier but providing faster approximate solutions.**
- **For small and medium inputs, CSP finds a perfect solution in under 100 iterations, while HC requires thousands of iterations in constrained cases but fewer iterations in more relaxed cases.**
- **HC is more scalable in relaxed scenarios, but its efficiency decreases significantly as problem constraints tighten, requiring more iterations and states to find acceptable solutions.**

### Qualitative Results
- **CSP**: Ensures a valid timetable but struggles with constrained scenarios (e.g., when no valid solution exists, it may run indefinitely or require significant time to fail). However, it is efficient when a solution is feasible.
- **HC**: Generates a near-optimal timetable in seconds but can fail to find a fully correct solution in highly constrained cases. It is more efficient when some flexibility in constraints is allowed.
- **Scalability**: CSP efficiently finds solutions when a valid timetable exists but does not scale well when constraints are too tight. HC scales better when some constraint violations are acceptable but becomes inefficient in strict constraint scenarios.
- **Flexibility**: HC can be tweaked with additional heuristics to handle larger instances, while CSP is rigid but guarantees correctness when a solution is possible.

## Conclusions
- **CSP is the best choice for one-time, high-accuracy scheduling problems where correctness is critical, especially for small and medium-sized problems with feasible solutions.**
- **HC is preferable when approximate solutions are acceptable, or when quick re-scheduling is needed, particularly for large and more flexible problems.**
- **For highly constrained problems, CSP should be used despite its computational cost, as it guarantees correctness. However, if constraints can be relaxed, HC may provide faster and reasonable solutions.**
- **Future improvements could include hybrid approaches combining CSP’s correctness with HC’s efficiency.**

## Usage
### Running the Hill Climbing Algorithm
```bash
python orar.py hc input_file
```

### Running the CSP Algorithm
```bash
python orar.py csp input_file
```

