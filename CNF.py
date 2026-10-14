from typing import List, Set


class Clause:
    def __init__(self, literals: Set[int]):
        self.literals = literals


class CNF:
    def __init__(self):
        self.clauses: List[Clause] = []
        self.assignments: List[int] = []

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
            self.assignments = [0] * self.n_literals

            for line in f.readlines():
                lits = line.split(" ")[:-1]
                self.clauses.append(Clause(literals=set(int(lit) for lit in lits)))

    def __deepcopy__(self, memo: dict[int, object]) -> "CNF":
        cnf = CNF()
        cnf.clauses = [Clause(set(clause.literals)) for clause in self.clauses]
        cnf.assignments = self.assignments.copy()
        cnf.n_clauses = self.n_clauses
        cnf.n_literals = self.n_literals
        return cnf

    # Convert F to F|l, where F|l is F, with l set to true. All clauses with l
    # (clause satisfaction) and all literals -l (unit resolution) are removed.
    #
    def restrict(self, assignment: int) -> None:
        self.clauses = [
            clause for clause in self.clauses if assignment not in clause.literals
        ]
        for clause in self.clauses:
            clause.literals.discard(-assignment)

        self.assignments[abs(assignment) - 1] = 1 if assignment > 0 else -1

    ##### PRINTING METHODS #####

    def print(self) -> None:
        print(f"p cnf {self.n_literals} {self.n_clauses}")
        for clause in self.clauses:
            for lit in clause.literals:
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
