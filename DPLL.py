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
        # resolve all unit clauses, as two watched literals doesnt work on them
        units = [clause[0] for clause in self.cnf.clauses if len(clause) == 1]
        # if both (l) and -(l) exist, the cnf is UNSAT
        if any(-u in units for u in units):
            return "UNSAT"
        # assign units on decision level 0
        for unit in units:
            self.cnf.assign(unit)

        def dpll() -> bool:
            if not self.propagate(cnf=self.cnf):
                return False

            x = self.cnf.pick()
            if not x:
                self.model = self.cnf.assignments[1:]
                return True

            for lit in [x, -x]:
                self.cnf.assign(lit, True)
                if dpll():
                    return True
                self.cnf.backtrack()
            return False

        return f"SAT: {self.model}" if dpll() else "UNSAT"

    # Two watched literals: watch clause[0] and clause[1] form every clause.
    # if either gets assigned to be false, an unassigned replacement is
    # searched. if none exists, its either satisfied (other watched is true),
    # a unit clause (other watched unassigned) or a conflict (other watched
    # also false).
    #
    @staticmethod
    def propagate(cnf: CNF) -> bool:
        while cnf.queue:
            false_lit = -cnf.queue.pop()

            watchers = cnf.watches[false_lit + cnf.n_literals]
            i = 0
            while i < len(watchers):
                clause = cnf.clauses[watchers[i]]

                if clause[0] == false_lit:
                    # if c[0] is false_lit, swap it to position 1
                    clause[0], clause[1] = clause[1], clause[0]

                # case 1: other watched is true, so continue
                #
                if cnf.value(clause[0]) == 1:
                    i += 1
                    continue

                # case 2: search some other non-false literal in clause
                #
                for k in range(2, len(clause)):
                    if cnf.value(clause[k]) != -1:
                        # swap false lit with non-false
                        clause[1], clause[k] = clause[k], clause[1]

                        # remove clause from lit watch list and add to c[1]'s
                        # watch list
                        c = watchers[i]
                        watchers[i] = watchers[-1]
                        watchers.pop()
                        cnf.watches[clause[1] + cnf.n_literals].append(c)

                        break

                # case 3: no replacement found, then either unit clause, when c[0]
                # is unassigned, or conflict
                #
                else:
                    if cnf.value(clause[0]) == -1:
                        cnf.queue.clear()
                        cnf.heap.bump(clause)
                        return False
                    cnf.assign(clause[0])
                    i += 1

        return True


if __name__ == "__main__":
    dpll = DPLL()
    dpll.read_cnf(sys.argv[1])
    start = time.time()
    print(dpll.solve())
    end = time.time()
    print("Solve time:", f"{end - start:>.2}", "sec")
