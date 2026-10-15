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

        def dpll() -> bool:
            if not self.resolve_and_propagate_unit_clauses(cnf=self.cnf):
                return False

            if all(self.cnf.satisfied):
                self.model = self.cnf.assignments
                return True

            x = self.cnf.pick_unassigned()
            for lit in [x, -x]:
                self.cnf.assign(lit, True)
                if dpll():
                    return True
                self.cnf.backtrack()
            return False

        return f"SAT: {self.model}" if dpll() else "UNSAT"

    # If a unit clause exists, its only literal l can only be true, otherwise
    # the formula is UNSAT. Setting l to true may create new unit clauses
    # which are resolved in succession until no unit clause exists anymore.
    #
    @staticmethod
    def resolve_and_propagate_unit_clauses(cnf: CNF) -> bool:
        changed = True
        while changed:
            changed = False

            # find unit clause
            for i, clause in enumerate(cnf.clauses):
                if cnf.satisfied[i]:
                    continue

                unassigned = [lit for lit in clause if not cnf.value(lit)]
                if not unassigned:
                    return False

                if len(unassigned) == 1:
                    cnf.assign(unassigned[0])
                    changed = True

        return True


if __name__ == "__main__":
    dpll = DPLL()
    dpll.read_cnf(sys.argv[1])
    start = time.time()
    print(dpll.solve())
    end = time.time()
    print(end - start)
