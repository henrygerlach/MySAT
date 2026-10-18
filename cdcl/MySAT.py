import sys
import time

from typing import List, Tuple

from CNF import CNF


class MySAT:
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
            conflict = self.propagate(self.cnf)

            if conflict >= 0:
                if len(self.cnf.trail) == 1:
                    return "UNSAT"
                learned, to_level = self.analyze(conflict)
                self.backtrack(to_level)
                self.cnf.add_clause(learned)
                self.cnf.assign(learned[0], reason=self.cnf.n_clauses - 1)
                continue

            x = self.cnf.pick()

            # no unassigned var left -> SAT
            if not x:
                self.models.append(self.cnf.assignments[1:])
                return "SAT"

            self.cnf.assign(x, True)
            self.flipped.append(False)

    def backtrack(self, to_level: int) -> None:
        while len(self.cnf.trail) - 1 > to_level:
            self.cnf.backtrack()
            self.flipped.pop()

    def analyze(self, conflict: int) -> Tuple[List[int], int]:
        conflict_clause = self.cnf.clauses[conflict]
        learned_clause: List[int] = conflict_clause.copy()

        while True:
            # find and count literals of the learned clause assigned on
            # current decision level
            n_literals = 0
            replacement_literals: List[int] = []
            for lit in self.cnf.trail[-1]:
                if -lit in learned_clause:
                    replacement_literals.append(lit)
                    n_literals += 1

            # if only one literal remains -> first UIP -> learned clause found
            if n_literals == 1:
                if len(learned_clause) > 1:
                    i = -1
                    highest_level = -1
                    for j, lit in enumerate(learned_clause):
                        if lit == -replacement_literals[0]:
                            continue
                        level = self.cnf.level[abs(lit)]
                        if level > highest_level:
                            i = j
                            highest_level = level
                    learned_clause[i], learned_clause[1] = (
                        learned_clause[1],
                        learned_clause[i],
                    )
                    k = learned_clause.index(-replacement_literals[0])
                    learned_clause[k], learned_clause[0] = (
                        learned_clause[0],
                        learned_clause[k],
                    )
                break

            # resolve literals with their reason clauses until learned_clause
            # contains only one literal from current decision level
            while n_literals > 1:
                replacement_literal = replacement_literals.pop()
                reason: int = self.cnf.reason[abs(replacement_literal)]  # type: ignore

                reason_clause = self.cnf.clauses[reason].copy()
                reason_clause.remove(replacement_literal)
                learned_clause.remove(-replacement_literal)
                learned_clause.extend(reason_clause)
                n_literals -= 1

                # remove duplicates
                learned_clause = list(set(learned_clause))

        return learned_clause, self.cnf.level[abs(learned_clause[1])] if len(
            learned_clause
        ) > 1 else 0

    # Two watched literals: watch clause[0] and clause[1] form every clause.
    # If either gets assigned to be false, an unassigned replacement is
    # searched. if none exists, its either satisfied (other watched is true),
    # a unit clause (other watched unassigned) or a conflict (other watched
    # also false).
    #
    @staticmethod
    def propagate(cnf: CNF) -> int:
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
                        return watchers[i]
                    cnf.assign(clause[0], reason=watchers[i])
                    i += 1

        return -1

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
    mysat = MySAT(sys.argv[1])

    solves = 1
    total_time = 0.0

    f = open(sys.argv[2], "w")
    f.write("N, Status, Time (s), Total Time (s)\n")
    for i in range(1, solves + 1):
        start = time.time()
        ret = mysat.solve()
        end = time.time()
        solve_time = end - start
        total_time += solve_time
        f.write(f"{i}, {ret}, {solve_time:>.2}, {total_time:>.2}\n")
