from typing import List

from Heap import Heap


class CNF:
    def __init__(self, input_path: str) -> None:
        self.clauses: List[List[int]] = []

        self.n_clauses: int = 0
        self.n_literals: int = 0

        # two-watched literals. the propagation queue is the trail itself:
        # everything from trail[qhead:] still has to be propagated
        self.qhead: int = 0
        self.watches: List[List[int]] = []

        # VSIDS + Phase saving
        self.heap: Heap
        self.phase: List[int] = []

        # bookkeeping
        self.assignments: List[int] = []
        self.trail: List[int] = []
        # trail_starts[d - 1] is the trail index where decision level d starts
        self.trail_starts: List[int] = []
        self.reason: List[int | None] = []
        self.level: List[int] = []

        # global seen list for analyze method, such that it is not
        # reinstantiated every conflict
        seen: List[bool] = []  # type: ignore  # noqa: F841

        self.read_cnf(input_path)
        self.reset()

    def read_cnf(self, path: str) -> None:
        with open(path, "r") as f:
            line = f.readline()
            while not line.startswith("p cnf "):
                line = f.readline()

            metadata = line.removesuffix("\n").split(" ")

            self.n_literals = int(metadata[2])
            self.n_clauses = int(metadata[3])

            for line in f.readlines():
                lits = line.split(" ")[:-1]
                self.clauses.append([int(lit) for lit in lits])

    # Reset the search state, for initialization or to prepare for the search
    # of another model
    #
    def reset(self) -> None:
        self.assignments = [0] * (2 * self.n_literals + 1)
        self.trail = []
        self.trail_starts = []
        self.reason = [-1] * (self.n_literals + 1)
        self.level = [-1] * (self.n_literals + 1)
        self.seen = [False] * (self.n_literals + 1)

        self.heap = Heap(self.n_literals)
        self.heap.seed(self.clauses)
        self.phase = [-1] * (self.n_literals + 1)

        self.qhead = 0
        self.watches = [[] for _ in range(2 * self.n_literals + 1)]
        for i, clause in enumerate(self.clauses):
            for lit in clause[:2]:
                self.watches[lit + self.n_literals].append(i)

    def add_clause(self, clause: List[int]) -> None:
        self.clauses.append(clause)
        self.n_clauses += 1

        if len(clause) == 1:
            # callers backtrack to level 0 before adding a unit clause
            self.assign(clause[0])
        else:
            for lit in clause[:2]:
                self.watches[lit + self.n_literals].append(self.n_clauses - 1)

    # Add assignment to global assignment array and trail (which also queues
    # it for propagation) and save the phase for the next decision (phase
    # saving)
    #
    def assign(
        self,
        lit: int,
        decision: bool = False,
        reason: int | None = None,
    ) -> None:
        var = abs(lit)

        # a decision opens a new level starting at the current trail end
        if decision:
            self.trail_starts.append(len(self.trail))
        self.trail.append(lit)

        value = 1 if lit > 0 else -1
        self.assignments[var] = value
        self.assignments[-var] = -value

        self.level[var] = len(self.trail_starts)
        self.reason[var] = reason

        self.phase[var] = self.assignments[var]

    # Revert assignments of all decision levels above to_level
    #
    def backtrack(self, to_level: int) -> None:
        if len(self.trail_starts) <= to_level:
            return

        start = self.trail_starts[to_level]
        for lit in self.trail[start:]:
            self.assignments[lit] = 0
            self.assignments[-lit] = 0

            # put unassigned vars back into the heap
            self.heap.insert(abs(lit))

        del self.trail[start:]
        del self.trail_starts[to_level:]
        self.qhead = start

    # Pick var for branching: VSIDS unassigned var with the highest acivity.
    # See more in Heap.py. Pick the phase according to the last assignments
    # phase
    #
    def pick(self) -> int:
        while (var := self.heap.pop()) and self.assignments[var]:
            pass
        return var * self.phase[var]

    # Add blocking clause to prepare for the search of another model
    #
    def add_blocking_clause(self, model: List[int]) -> None:
        blocking_clause: List[int] = [-lit for lit in model]
        self.clauses.append(blocking_clause)
        self.n_clauses += 1

    ##### PRINTING METHODS #####

    def print(self) -> None:
        print(f"p cnf {self.n_literals} {self.n_clauses}")
        for clause in self.clauses:
            for lit in clause:
                print(f"{lit} ", end="")
            print("0")

    def print_assignments(self) -> None:
        width = max(len(str(len(self.assignments))), 2)
        for start in range(0, len(self.assignments), 20):
            row = self.assignments[start : start + 20]
            print(
                " ".join(
                    f"{i:>{width}}" for i in range(start + 1, start + len(row) + 1)
                )
            )
            print(" ".join(f"{a:>{width}}" for a in row))
            print()

    def print_trail(self) -> None:
        level_width = len(str(len(self.trail_starts)))
        lit_width = len(str(self.n_literals)) + 1
        bounds = [0] + self.trail_starts + [len(self.trail)]
        for i in range(len(bounds) - 1):
            level = self.trail[bounds[i] : bounds[i + 1]]
            print(f"@{i:>{level_width}} |", end="")
            for assignment in level:
                print(f" {assignment:>{lit_width}}", end="")
            print()
