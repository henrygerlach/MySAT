from typing import List

from Heap import Heap


class CNF:
    def __init__(self, input_path: str) -> None:
        self.clauses: List[List[int]] = []

        self.n_clauses: int = 0
        self.n_literals: int = 0

        # two-watched literals
        self.queue: List[int] = []
        self.watches: List[List[int]] = []

        # VSIDS + Phase saving
        self.heap: Heap
        self.phase: List[int] = []

        # bookkeeping
        self.assignments: List[int] = []
        self.trail: List[List[int]] = [[]]
        self.reason: List[int | None] = []
        self.level: List[int] = []

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
        self.assignments = [0] * (self.n_literals + 1)
        self.trail = [[]]

        self.reason = [-1] * (self.n_literals + 1)
        self.level = [-1] * (self.n_literals + 1)

        self.heap = Heap(self.n_literals)
        self.heap.seed(self.clauses)
        self.phase = [-1] * (self.n_literals + 1)

        self.queue = []
        self.watches = [[] for _ in range(2 * self.n_literals + 1)]
        for i, clause in enumerate(self.clauses):
            for lit in clause[:2]:
                self.watches[lit + self.n_literals].append(i)

    def add_clause(self, clause: List[int]) -> None:
        self.clauses.append(clause)
        self.n_clauses += 1

        if len(clause) == 1:
            self.assign(clause[0], level=0)
        else:
            for lit in clause[:2]:
                self.watches[lit + self.n_literals].append(self.n_clauses - 1)

    # Add assignment to global assignment array and trail, append the lit to
    # the propagation queue and save the phase for the next decision (phase
    # saving)
    #
    def assign(
        self,
        lit: int,
        decision: bool = False,
        reason: int | None = None,
        level: int = -1,
    ) -> None:
        var = abs(lit)

        if decision:
            self.trail.append([lit])
        else:
            self.trail[level].append(lit)

        self.assignments[var] = 1 if lit > 0 else -1
        self.level[var] = level if level != -1 else len(self.trail) - 1

        self.reason[var] = reason

        self.phase[var] = self.assignments[var]

        self.queue.append(lit)

    # Revert assignments of the last decision level
    #
    def backtrack(self, to_level: int) -> None:
        while len(self.trail) - 1 > to_level:
            for lit in self.trail.pop():
                self.assignments[abs(lit)] = 0

                # put unassigned vars back into the heap
                self.heap.insert(abs(lit))

    # Evaluate truth value of literal: Return 1 if lit is true, -1 if false
    # and 0 if unassigned
    #
    def value(self, lit: int) -> int:
        value = self.assignments[abs(lit)]
        return value if lit > 0 else -value

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
        level_width = len(str(len(self.trail)))
        lit_width = len(str(self.n_literals)) + 1
        for i, level in enumerate(self.trail):
            print(f"@{i:>{level_width}} |", end="")
            for assignment in level:
                print(f" {assignment:>{lit_width}}", end="")
            print()
