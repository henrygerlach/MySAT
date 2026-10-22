# Modern SAT Solving: MySAT

## The SAT Problem

The SAT (Satisfiability) Problem is one of the most known problems in computer science. Even though it is not that hard to understand it is quite difficult to solve efficiently, especially on large instances. 

The problem is especially important as it was the first problem proofed to be *NP-complete* (1971 - Cook-Levin-Theorem), which means that all problems which have an algorithm solving it in polynomial (P) or non-polynomial (NP) time are reducible to this problem. Reduciable means, that there exists an algorithm that transforms an instance of a problem into an instance of another problem in polynomial time and that the solutions of the reduced to instance provide solutions for the original problem. For example a Soduko grid can be transformed into a SAT formula in polynomial time. Solving this formula provides solutions for the Soduko grid.

A SAT or CNF (conjuncitve normal form) formula consists of AND connected clauses, where each clause is an OR of literals (`x` or `¬x`). CNF formulas are stored in files with the DIMACS format. There variables are numbers, a negative number means a negated literal, and `0` ends a clause:

```cnf
p cnf 3 2
1 -2 0
2 3 0
```

## Historic Approach: DPLL

DPLL (Davis-Putman-Logemann-Loveland) (1960 and 1962) is the or one of the first functional SAT solving algorithms.

### The core operation: `F|l`

Everthing is build around the core operation `F|l`, where `F` is the original formula and `l` is a literal set to true. Transforming `F` to `F|l`:

* every clause containing `l` is satisfied, so it is removed,
* every occurrence of `¬l` is false, so it is removed from its clause.

Two end states fall out of this:

* `F` is empty (no clauses left): every clause is satisfied → SAT.
* `F` contains the empty clause `□` (all its literals were removed): that clause can’t be satisfied under the current assignment → conflict.

### The Algorithm 

**Unit propagation**. If `F` contains a unit clause `(l)`, replace `F` by `F|l`. This can be performed because all models must make `l` true for the unit clause to be true. If `l` is false, then the formula becomes UNSAT.

**BCP (Boolean Constraint Propagation)**: Applying unit propagation often creates new unit clauses, which then can be resolved aswell until no new is created.

**Pure Literal Elimination**: If a literal `l` occurs in `F` but `¬l` never does, replace `F` by `F|l`. This preserves satisfiability, but not equivalence, as `F` may have models with `l` being false, but `F|l` has set `l` to true forever.

**Splitting**: Pick an unassigned variable `x`. Then `F` is SAT iff `F|x` is SAT or `F|¬x` is SAT (Shannon expansion). Try one, and if it fails, try the other.

```
DPLL(F):
    while F has a unit clause (l):  F := F|l
    if □ ∈ F:  return UNSAT
    for each pure literal l:        F := F|l
    if F = ∅:  return SAT
    x := choose a variable              # branching heuristic
    return DPLL(F|x) or DPLL(F|¬x)
```

### Implementation

The naive approach is to copy the CNF every recursion step, to delete clauses and remove literals inplace. To avoid this, one can implement a trail data strucutre, which is a 2D list, where each variable decision creates a new layer and each propagated literal afterwards is added to this layer. If then the algorithm backtracks, pop the last layer and unassign all literals from that layer. 

#### Further Improvements

**Two-Watched Literals**: Propagation only needs to find two kinds of clauses. Unit clauses, all literals but one are false and conflicting clauses, where all literals are false.

A clause with at least two non-false literals (two-watched literals) is neither, so it can be ignored. Only if one of them turns false something must happen. There are three cases:
1. The other watch is true: the clause is satisfied. Do nothing.
2. Some other literal in the clause is not false: move the watch to that literal. Two non-false watched literals again.
3. If there is no replacement and the other watched is unassigned, the clause is unit -> assign the other watched. Otherwise, if the other watched is false, its a conflict -> backtrack.

**VSIDS**: A variable decision heuristic, which keeps an acitivity score for each variable. The score is increased if a clause that includes it is involved in conflict analysis. On variable decision the unassigned variable with the highest score is choosen. This keeps the search focused on clauses involved in recent conflicts.

**Phase Saving**: On each assignment save the phase. On the next variable decision pick the last assigned phase first.

## Modern SAT Solving: CDCL

The problem with DPLL is its chronological backtracking (undoing the most recent decisions on conflict, until a free branch is found). If the real problem of the subtree are decisions on lower decision levels, it tries every subtree based on those decisions before backtracking and resolving them. This can be mitigated by using CDCL.

**CDCL (Clause-Driven Clause Learning)** is DPLL plus a major change. When a conflict happens (all literals in a clause are false), the solver works out why it happend and adds a reason clause, preventing the conflict from occuring again. Then it backtracks to the decision level the newly added clause first becomes useful.

**Implication Graph**: Consider each assigned literal to be a node in a graph and κ a special conflict node. The edges between the nodes are the implications. For a clause c, if all literals but one is false, the left over literal is forced to be true and is thus implied by all other negated literals. A decision has no incoming edges, as it is not implied by any other literals.

**Conflict Analysis**: Take any cut through the graph that separates all the decisions from κ. The literals on the decision side of the cut that have an edge crossing the cut cannot all be true at once, because together they imply the conflict. So the clause made of their negations is a valid learned clause.

**UIP (Unique Implication Point)** is a literal at the current decision level that every path from the current decision to the conflict passes through. The decision is always a UIP, but there may be other ones closer to the conflict.

*Which cut to choose?* An asserting clause is desired, which contains exactly one literal (UIP) form the current level, such that on a backtrack the clause immediately becomes unit and forces something new. It has been shown that choosing the first UIP (the UIP closest to the conflict) produces the best results.

### The Algorithm

For each variable store $level[v]$ (the decision level at which $v$ was assigned) and $reason[v]$ (the clause that forced $v$, or $None$ if $v$ was a decision)

Start with the conflict clause. Then repeat:

1. Take the current-level literal in the clause that was assigned most recently on the trail.
2. Replace it with the other literals of its reason clause. This is a resolution step on that variable.
3. Stop as soon as exactly one current-level literal is left in the to be learned clause. That literal is the first UIP.

Literals from lower levels stay in the clause unchanged, and level-0 literals are dropped.

### Backjumping

After learning a clause, the solver views the decision levels of the other literals in the learned clause and jumps to the highest of them. This instantly turns the learned clause unit, forcing a new search space.

### Restarts

**LBD (Literal Block Distance)** is the number of distinct decisions levels among the literals of a learned clause. It measures a form a clause quality, as it counts how many distinct decisions formed the clause. If the LBD is high, then many decisions were involved making it unlikely the clause will do something in propagate in the future. But if the LBD is low, then only a few decisions were involved, making the clause very likely to take part in propagation again, making them really valuable.

**Restarts**: The idea behind restarts is that if the LBD of the clauses the solver has learned recently are worse than the long-term average, the solver is stuck i an unproductive part of the search, so it restarts. While it keeps learning good clauses, it doesn't restart.

* Restarting means just backtracking to level 0, keeping VSIDS scores and saved phases.

For this the solver keeps two exponential moving averages of the LBDs of learned clauses:

* fast: an average over roughly the last 30 conflicts (α ≈ 1/32)
* slow: an average over a long horizon (α ≈ 1/10⁴ to 1/10⁵)

After each conflict, update both with `ema += α * (lbd - ema)`. Then restart if: `fast > 1.1 * slow`

* EMA warm-up: both averages start at 0, so early values are biased low. Either skip restarts for the first ~50 conflicts, or use bias correction as CaDiCaL does: divide by 1 - (1-α)^n.
* Minimum interval: CaDiCaL's restartint is 2 conflicts. Without some minimum, the solver can restart on every conflict.