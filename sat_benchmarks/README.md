# Test CNFs for DPLL

All answers were verified with CaDiCaL. Each file also states its expected result in a `c expected:` comment line.
"Naive DPLL" = the iterative version from dpll/DPLL.py (rescans all clauses on every propagation round, branches on the lowest unassigned variable, true first).

| File | Vars | Clauses | Expected | Naive DPLL (Python) |
|---|---|---|---|---|
| rand3_n20_sat.cnf | 20 | 85 | SAT | instant, 6 conflicts |
| rand3_n20_unsat.cnf | 20 | 85 | UNSAT | instant, 32 conflicts |
| php_5_4.cnf | 20 | 45 | UNSAT | instant, 52 conflicts |
| php_6_5.cnf | 30 | 81 | UNSAT | instant, 375 conflicts |
| rand3_n50_sat.cnf | 50 | 213 | SAT | < 1 s, 124 conflicts |
| rand3_n50_unsat.cnf | 50 | 213 | UNSAT | < 1 s, 169 conflicts |
| php_7_6.cnf | 42 | 133 | UNSAT | < 1 s, 3,246 conflicts |
| php_8_7.cnf | 56 | 204 | UNSAT | 5 s, 32,781 conflicts |
| rand3_n100_sat.cnf | 100 | 426 | SAT | 30 s, 37,311 conflicts |
| rand3_n100_unsat.cnf | 100 | 426 | UNSAT | 23 s, 29,338 conflicts |
| sudoku.cnf | 729 | 3,270 | SAT | did not finish in 4 min |

## Families

- **rand3_***: random 3-SAT with 4.26 clauses per variable, the phase transition where random instances are hardest.
- **php_P_H**: pigeonhole principle, P pigeons into H holes. Variable `i*H + j + 1` means pigeon i sits in hole j (0-based). Always UNSAT, and exponentially hard for every resolution-based solver, so the conflict count grows roughly 10x per step.
- **sudoku.cnf**: a standard Sudoku. Variable `81*row + 9*col + digit + 1` (all 0-based) means the cell holds that digit. Large but structurally easy: good branching plus fast propagation solves it with almost no search. Decode a model by taking the positive literals.
