import sys
import time

from typing import List, Tuple

from CNF import CNF


class MySAT:
    def __init__(self, input_path: str):
        self.cnf: CNF = CNF(input_path)

        self.models: List[List[int]] = []

    # Solving a CNF is done by propagating unit clauses and if none exists
    # currently, propagating a variable choosen by VSIDS. On conflict add a
    # learned clause to prevent the conflcit from occuring again. If all
    # branches are tried without success -> UNSAT. If all variables are
    # assigned without conflict -> SAT.
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

        # add blocking clause to block same model to be found again
        elif not self.block_model():
            return "UNSAT"

        while True:
            conflict = self.propagate()

            # on conflict, if on decision level 0 => UNSAT, because clause
            # forced unsatisfied by level 0 decisions. else learn clause,
            # backjump, add learned clause and assign first UIP, to enter new
            # search space
            if conflict >= 0:
                if len(self.cnf.trail) == 1:
                    return "UNSAT"
                learned, to_level = self.analyze(conflict)
                self.cnf.backtrack(to_level)
                self.cnf.add_clause(learned)
                self.cnf.assign(learned[0], reason=self.cnf.n_clauses - 1)
                continue

            # pick var using VSIDS and phase saving
            x = self.cnf.pick()

            # no unassigned var left -> SAT
            if not x:
                self.models.append(self.cnf.assignments[1:])
                return "SAT"

            self.cnf.assign(x, True)

    # Propagte unit clauses until none is left or a conflict (all literals in
    # a clause evalutate to false) is found.
    #
    # Two watched literals: watch clause[0] and clause[1] form every clause.
    # If either gets assigned to be false, an unassigned replacement is
    # searched. If none exists, its either satisfied (other watched is true),
    # a unit clause (other watched unassigned) or a conflict (other watched
    # also false).
    #
    def propagate(self) -> int:
        while self.cnf.queue:
            false_lit = -self.cnf.queue.pop()

            watchers = self.cnf.watches[false_lit + self.cnf.n_literals]
            i = 0
            while i < len(watchers):
                clause = self.cnf.clauses[watchers[i]]

                # if c[0] is false_lit, swap it to position 1
                if clause[0] == false_lit:
                    clause[0], clause[1] = clause[1], clause[0]

                # case 1: other watched is true, so continue
                #
                if self.cnf.value(clause[0]) == 1:
                    i += 1
                    continue

                # case 2: search some other non-false literal in clause
                #
                for k in range(2, len(clause)):
                    if self.cnf.value(clause[k]) != -1:
                        # swap false lit with non-false
                        clause[1], clause[k] = clause[k], clause[1]

                        # remove clause from lit watch list and add to c[1]'s
                        # watch list
                        c = watchers[i]
                        watchers[i] = watchers[-1]
                        watchers.pop()
                        self.cnf.watches[clause[1] + self.cnf.n_literals].append(c)

                        break

                # case 3: no replacement found, then either unit clause, when c[0]
                # is unassigned, or conflict
                #
                else:
                    if self.cnf.value(clause[0]) == -1:
                        self.cnf.queue.clear()
                        self.cnf.heap.bump(clause)
                        return watchers[i]
                    self.cnf.assign(clause[0], reason=watchers[i])
                    i += 1

        return -1

    # On conflict, find learned clause to prevent the same conflict from
    # occuring again.
    #
    def analyze(self, conflict: int) -> Tuple[List[int], int]:
        cur_level = len(self.cnf.trail) - 1
        seen: List[bool] = [False] * (self.cnf.n_literals + 1)

        learned: List[int] = [0]
        counter = 0
        clause: List[int] = self.cnf.clauses[conflict]
        i = len(self.cnf.trail[-1])

        while True:
            # Step 1: Take the literals of clause (initially conflict clause)
            #
            for lit in clause:
                var = abs(lit)

                # if already seen, continue. else set to seen
                if seen[var]:
                    continue
                seen[var] = True

                # when lit on cur_level then increment counter, else append to
                # learned clause (the lit is already final for the learned
                # clause)
                if self.cnf.level[var] == cur_level:
                    counter += 1
                elif self.cnf.level[var] > 0:
                    learned.append(lit)

            # Step 2: Find next literal to resolve, by walking the trail from
            # back to front, restarting the search at the last resolved
            # literal and looking for the next literal that is marked seen
            #
            i -= 1
            while not seen[abs(self.cnf.trail[cur_level][i])]:
                i -= 1

            pending = self.cnf.trail[cur_level][i]
            counter -= 1

            # Step 3: Is pending the only literal left? If yes, pending is the
            # first UIP
            #
            if not counter:
                break

            # Step 4: Set the reason clause of pending to the next clause to
            # resolve
            reason = self.cnf.reason[abs(pending)]
            clause = self.cnf.clauses[reason if reason else 0]

        # setting learned[0] to negated first UIP
        learned[0] = -pending

        # if learned clause is unit, it should backtrack to level 0
        if len(learned) == 1:
            return learned, 0

        # swap the literal with the second highest assignment level to
        # position 1
        i_max = learned.index(max(learned[1:], key=lambda x: self.cnf.level[abs(x)]))
        learned[1], learned[i_max] = learned[i_max], learned[1]
        return learned, self.cnf.level[abs(learned[1])]

    # If models already found, add blocking clause blocking all decisions made
    # on the way towards the model, forcing new decisions.
    #
    def block_model(self) -> bool:
        # create blocking clause from the negated decision that lead to the
        # last model
        blocking = [
            -self.cnf.trail[level][0] for level in range(len(self.cnf.trail) - 1, 0, -1)
        ]

        # model was found on level 0, thus there is no other model
        if not blocking:
            return False

        # backtrack one level, add the blocking clause and assign the first
        # literal with its negated latest decision to force a new search space
        self.cnf.backtrack(len(self.cnf.trail) - 2)
        self.cnf.add_clause(blocking)
        if len(blocking) > 1:
            self.cnf.assign(blocking[0], reason=self.cnf.n_clauses - 1)

        return True


if __name__ == "__main__":
    mysat = MySAT(sys.argv[1])

    solves = 3
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
