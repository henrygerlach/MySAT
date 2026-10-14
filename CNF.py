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
                self.add_clause(clause=Clause(literals=set(int(lit) for lit in lits)))

    def add_clause(self, clause: Clause) -> None:
        self.clauses.append(clause)

    def __deepcopy__(self, memo: dict[int, object]) -> "CNF":
        cnf = CNF()
        cnf.clauses = [Clause(set(clause.literals)) for clause in self.clauses]
        cnf.assignments = self.assignments.copy()
        cnf.n_clauses = self.n_clauses
        cnf.n_literals = self.n_literals
        return cnf

    ##### DDPL METHODS #####

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

    # If a unit clause exists, its only literal l can only be true, otherwise
    # the formula is UNSAT. Setting l to true may create new unit clauses
    # which are resolved in succession until no unit clause exists anymore.
    #
    def resolve_and_propagate_unit_clauses(self) -> None:
        while True:
            i = 0
            while i < len(self.clauses) and len(self.clauses[i].literals) != 1:
                i += 1

            if i < len(self.clauses):
                lit = 0
                for literal in self.clauses[i].literals:
                    lit = literal
                    break
                self.restrict(lit)
            else:
                break

    # If in a formula a variable x only occurs as x and not as -x, it can be
    # set to true.
    #
    def remove_pure_literals(self) -> None:
        literals: List[set[int]] = [set() for _ in range(self.n_literals + 1)]
        for clause in self.clauses:
            for literal in clause.literals:
                literals[abs(literal)].add(literal)

        for literal in literals:
            if len(literal) == 1:
                self.restrict(list(literal)[0])

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
