import copy
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
                cnf.restrict(x)

            cnf.resolve_and_propagate_unit_clauses()

            for clause in cnf.clauses:
                if not clause.literals:
                    return False

            cnf.remove_pure_literals()

            if not len(cnf.clauses):
                self.model = cnf.assignments
                return True

            x = 0
            for lit in cnf.clauses[0].literals:
                x = lit
                break
            return dpll(copy.deepcopy(cnf), x) or dpll(cnf, -x)

        return f"SAT: {self.model}" if dpll(copy.deepcopy(self.cnf)) else "UNSAT"


if __name__ == "__main__":
    dpll = DPLL()
    dpll.read_cnf(sys.argv[1])
    start = time.time()
    print(dpll.solve())
    end = time.time()
    print(end - start)
