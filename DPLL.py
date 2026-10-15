import sys
import time

from typing import List

from CNF import CNF


class DPLL:
    def __init__(self):
        self.cnf: CNF = CNF()

        self.model: List[int] = []

    def read_cnf(self, path: str) -> None:
        self.cnf.read_cnf(path=path)

    def solve(self) -> str:

        def dpll(cnf: CNF, x: int | None = None) -> bool:
            if x:
                cnf.assign(x, True)

            self.resolve_and_propagate_unit_clauses(cnf=cnf)

            for i, clause in enumerate(cnf.clauses):
                if cnf.satisfied[i]:
                    continue

                assignment_sum = sum(
                    abs(cnf.assignments[abs(lit) - 1]) for lit in clause
                )

                if assignment_sum == len(clause):
                    cnf.backtrack()
                    return False

            if all(cnf.satisfied):
                self.model = cnf.assignments
                return True

            x = cnf.pick_unassigned()
            if dpll(cnf, x) or dpll(cnf, -x):
                return True

            cnf.backtrack()
            return False

        return f"SAT: {self.model}" if dpll(self.cnf) else "UNSAT"

    # If a unit clause exists, its only literal l can only be true, otherwise
    # the formula is UNSAT. Setting l to true may create new unit clauses
    # which are resolved in succession until no unit clause exists anymore.
    #
    @staticmethod
    def resolve_and_propagate_unit_clauses(cnf: CNF) -> None:
        changed = True
        while changed:
            changed = False

            # find unit clause
            for i, clause in enumerate(cnf.clauses):
                # continue if clause is already satisfied
                if cnf.satisfied[i]:
                    continue

                # check if unit clause
                i_unassigned = -1
                assignment_sum = 0
                for i, lit in enumerate(clause):
                    assigned = abs(cnf.assignments[abs(lit) - 1])
                    assignment_sum += assigned

                    if not assigned:
                        i_unassigned = i

                # assign l
                if assignment_sum == len(clause) - 1:
                    cnf.assign(clause[i_unassigned])
                    changed = True


if __name__ == "__main__":
    dpll = DPLL()
    dpll.read_cnf(sys.argv[1])
    start = time.time()
    print(dpll.solve())
    end = time.time()
    print(end - start)
