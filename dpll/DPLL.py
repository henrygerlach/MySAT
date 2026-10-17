import sys
import time

from typing import List

from dpll.CNF import CNF


class DPLL:
    def __init__(self, input_path: str):
        self.cnf: CNF = CNF(input_path)

        self.models: List[List[int]] = []

        # flipped[i] is True, if the decision on level i + 1 is already the
        # flipped branch -x. every new decision level appends False to flipped
        # when the flipped decision is tried it is set to True. On conflict all
        # already flipped decisions are unmade (backtracking) until a decision
        # is found, which has its flipped decision still open - trying it. When
        # the backtrack hits level 0, all branches were tried and thus its
        # UNSAT.
        self.flipped: List[bool] = []

    # Solving a CNF is done by propagating unit clauses and if none exists
    # currently, propagating a variable choosen by VSIDS. If all branches are
    # tried without succes -> UNSAT. If all variables are assigned without
    # conflict -> SAT.
    #
    def solve(self) -> str:
        if not self.models:
            # resolve all unit clauses, as two watched literals doesnt work on them
            units = [clause[0] for clause in self.cnf.clauses if len(clause) == 1]
            # if both (l) and -(l) exist, the cnf is UNSAT
            if any(-u in units for u in units):
                return "UNSAT"
            # assign units on decision level 0
            for unit in units:
                self.cnf.assign(unit)

        # if models where found before, and another solve comes in to find
        # another model. Handle the satisfying branch as conflict and search
        # another branch.
        elif not self.next_branch():
            return "UNSAT"

        while True:
            if not self.propagate(self.cnf):
                if not self.next_branch():
                    return "UNSAT"
                continue

            x = self.cnf.pick()

            # no unassigned var left -> SAT
            if not x:
                self.models.append(self.cnf.assignments[1:])
                return "SAT"

            self.cnf.assign(x, True)
            self.flipped.append(False)

    # Two watched literals: watch clause[0] and clause[1] form every clause.
    # If either gets assigned to be false, an unassigned replacement is
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

    # Backtrack all already flipped decisions and flip latest not yet flipped
    # decision
    def next_branch(self) -> bool:
        while self.flipped and self.flipped[-1]:
            self.cnf.backtrack()
            self.flipped.pop()

        # if no flipped decision is too be made -> all branches tried
        # and conflict -> UNSAT
        if not self.flipped:
            return False

        # try the flipped branch of the last decision
        x = self.cnf.trail[-1][0]
        self.cnf.backtrack()
        self.cnf.assign(-x, True)
        self.flipped[-1] = True
        return True


if __name__ == "__main__":
    dpll = DPLL(sys.argv[1])

    solves = 100
    total_time = 0.0

    f = open(sys.argv[2], "w")
    f.write("N, Time (s), Total Time (s)\n")
    for i in range(1, solves + 1):
        start = time.time()
        ret = dpll.solve()
        end = time.time()
        solve_time = end - start
        total_time += solve_time
        f.write(f"{i}, {solve_time:>.2}, {total_time:>.2}\n")
