from typing import List


class CNF:
    def __init__(self):
        self.clauses: List[List[int]] = []
        self.satisfied: List[bool] = []
        self.assignments: List[int] = []
        self.trail: List[List[int]] = [[]]

        self.n_clauses: int = 0
        self.n_literals: int = 0

    def read_cnf(self, path: str) -> None:
        with open(path, "r") as f:
            line = f.readline()
            while not line.startswith("p cnf "):
                line = f.readline()

            metadata = line.removesuffix("\n").split(" ")

            self.n_literals = int(metadata[2])
            self.n_clauses = int(metadata[3])
            self.satisfied = [False] * self.n_clauses
            self.assignments = [0] * self.n_literals

            for line in f.readlines():
                lits = line.split(" ")[:-1]
                self.clauses.append([int(lit) for lit in lits])

    # Add assignment to global assignment array and trail. And keep track
    # of satisfied clauses
    #
    def assign(self, assignment: int, decision: bool = False) -> None:
        self.assignments[abs(assignment) - 1] = 1 if assignment > 0 else -1

        if decision:
            self.trail.append([assignment])
        else:
            self.trail[-1].append(assignment)

        for i, clause in enumerate(self.clauses, 0):
            if self.satisfied[i]:
                continue

            if assignment in clause:
                self.satisfied[i] = True

    # Revert assignments of the last decision level(s)
    #
    def backtrack(self, levels: int = 1):
        for _ in range(1, levels + 1):
            level = self.trail.pop()
            for assignment in level:
                self.assignments[abs(assignment) - 1] = 0

        self.satisfied = [False] * self.n_clauses
        for i, clause in enumerate(self.clauses):
            for lit in clause:
                assignment = self.assignments[abs(lit) - 1]
                if (assignment > 0 and lit > 0) or (assignment < 0 and lit < 0):
                    self.satisfied[i] = True

    # pick the first literal from the first unsatisfied clause
    #
    def pick_unassigned(self) -> int:
        for i, clause in enumerate(self.clauses):
            if self.satisfied[i]:
                continue

            for lit in clause:
                if not self.assignments[abs(lit) - 1]:
                    return lit

        return 0

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
