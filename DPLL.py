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

            self.resolve_and_propagate_unit_clauses(cnf=cnf)

            for clause in cnf.clauses:
                if not clause:
                    return False

            self.remove_pure_literals(cnf=cnf)

            if not len(cnf.clauses):
                self.model = cnf.assignments
                return True

            x = 0
            for lit in cnf.clauses[0]:
                x = lit
                break
            return dpll(copy.deepcopy(cnf), x) or dpll(cnf, -x)

        return f"SAT: {self.model}" if dpll(copy.deepcopy(self.cnf)) else "UNSAT"

    # If a unit clause exists, its only literal l can only be true, otherwise
    # the formula is UNSAT. Setting l to true may create new unit clauses
    # which are resolved in succession until no unit clause exists anymore.
    #
    @staticmethod
    def resolve_and_propagate_unit_clauses(cnf: CNF) -> None:
        while True:
            i = 0
            while i < len(cnf.clauses) and len(cnf.clauses[i]) != 1:
                i += 1

            if i < len(cnf.clauses):
                lit = 0
                for literal in cnf.clauses[i]:
                    lit = literal
                    break
                cnf.restrict(lit)
            else:
                break

    # If in a formula a variable x only occurs as x and not as -x, it can be
    # set to true.
    #
    @staticmethod
    def remove_pure_literals(cnf: CNF) -> None:
        literals: List[set[int]] = [set() for _ in range(cnf.n_literals + 1)]
        for clause in cnf.clauses:
            for literal in clause:
                literals[abs(literal)].add(literal)

        for literal in literals:
            if len(literal) == 1:
                cnf.restrict(list(literal)[0])


if __name__ == "__main__":
    dpll = DPLL()
    dpll.read_cnf(sys.argv[1])
    start = time.time()
    print(dpll.solve())
    end = time.time()
    print(end - start)
