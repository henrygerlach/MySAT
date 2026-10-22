import sys
import time

from typing import List, Tuple

from CNF import CNF


# restart constants
ALPHA_FAST = 1 / 32
ALPHA_SLOW = 1e-5
RESTART_MARGIN = 1.1
RESTART_INT = 2


class MySAT:
    def __init__(self, input_path: str):
        self.cnf: CNF = CNF(input_path)

        self.models: List[List[int]] = []
        self.ret: str | None = None

        # restart vars
        self.biased_fast: float = 0.0
        self.biased_slow: float = 0.0
        self.exp_fast: float = 1.0
        self.exp_slow: float = 1.0
        self.conflicts_since_restart: int = 0

    # Solving a CNF is done by propagating unit clauses and if none exists
    # currently, propagating a variable choosen by VSIDS. On conflict add a
    # learned clause to prevent the conflcit from occuring again. If all
    # branches are tried without success -> UNSAT. If all variables are
    # assigned without conflict -> SAT.
    #
    def solve(self) -> str:
        cnf = self.cnf

        if self.ret != "UNSAT":
            # resolve all unit clauses, as two watched literals doesnt work on them
            units = set(clause[0] for clause in cnf.clauses if len(clause) == 1)
            # if both (l) and -(l) exist, the cnf is UNSAT
            if any(-u in units for u in units):
                return "UNSAT"
            # assign units on decision level 0
            for unit in units:
                cnf.assign(unit)

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
                if not cnf.trail_starts:
                    self.ret = "UNSAT"
                    return "UNSAT"

                learned, to_level, lbd = self.analyze(conflict)

                cnf.backtrack(to_level)
                cnf.add_asserting_clause(learned)

                self.restart(lbd)

                continue

            # pick var using VSIDS and phase saving
            x = cnf.pick()

            # no unassigned var left -> SAT
            if not x:
                self.models.append(cnf.assignments[1 : cnf.n_literals + 1])
                return "SAT"

            cnf.assign(x, True)

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
        cnf = self.cnf

        # FIFO: propagate the trail from qhead in assignment order
        while cnf.qhead < len(cnf.trail):
            false_lit = -cnf.trail[cnf.qhead]
            cnf.qhead += 1

            watchers = cnf.watches[false_lit + cnf.n_literals]
            i = 0
            while i < len(watchers):
                clause = cnf.clauses[watchers[i]]

                # if c[0] is false_lit, swap it to position 1
                if clause[0] == false_lit:
                    clause[0], clause[1] = clause[1], clause[0]

                # case 1: other watched is true, so continue
                #
                if cnf.assignments[clause[0]] == 1:
                    i += 1
                    continue

                # case 2: search some other non-false literal in clause
                #
                for k in range(2, len(clause)):
                    if cnf.assignments[clause[k]] != -1:
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
                    if cnf.assignments[clause[0]] == -1:
                        cnf.qhead = len(cnf.trail)
                        return watchers[i]
                    cnf.assign(clause[0], reason=watchers[i])
                    i += 1

        return -1

    # On conflict, find learned clause to prevent the same conflict from
    # occuring again.
    #
    def analyze(self, conflict: int) -> Tuple[List[int], int, int]:
        cnf = self.cnf
        cur_level = len(cnf.trail_starts)

        seen = cnf.seen
        marked: List[int] = []

        learned: List[int] = [0]
        counter = 0
        clause: List[int] = cnf.clauses[conflict]
        i = len(cnf.trail)

        while True:
            # Step 1: Take the literals of clause (initially conflict clause)
            #
            for lit in clause:
                var = abs(lit)

                # if already seen, continue. else set to seen
                if seen[var]:
                    continue
                seen[var] = True
                marked.append(var)
                cnf.heap.bump(lit)

                # when lit on cur_level then increment counter, else append to
                # learned clause (the lit is already final for the learned
                # clause)
                if cnf.level[var] == cur_level:
                    counter += 1
                elif cnf.level[var] > 0:
                    learned.append(lit)

            # Step 2: Find next literal to resolve, by walking the trail from
            # back to front, restarting the search at the last resolved
            # literal and looking for the next literal that is marked seen
            #
            i -= 1
            while not seen[abs(cnf.trail[i])]:
                i -= 1

            pending = cnf.trail[i]
            counter -= 1

            # Step 3: Is pending the only literal left? If yes, pending is the
            # first UIP
            #
            if not counter:
                break

            # Step 4: Set the reason clause of pending to the next clause to
            # resolve
            reason = cnf.reason[abs(pending)]
            clause = cnf.clauses[reason if reason else 0]

        # decay VSIDS activity scores once per conflict
        cnf.heap.decay()

        # setting learned[0] to negated first UIP
        learned[0] = -pending

        # unmark all seen variables for next analyze run
        for var in marked:
            seen[var] = False

        # calculate lbd (literal block distance) - # of distinct levels in
        # learned clause
        lbd = len({cnf.level[abs(lit)] for lit in learned})

        # if learned clause is unit, it should backtrack to level 0
        if len(learned) == 1:
            return learned, 0, lbd

        # swap the literal with the second highest assignment level to
        # position 1
        i_max = 0
        level_max = -1
        for i, lit in enumerate(learned[1:], 1):
            level = cnf.level[abs(lit)]
            if level > level_max:
                i_max = i
                level_max = level
        learned[1], learned[i_max] = learned[i_max], learned[1]

        return learned, cnf.level[abs(learned[1])], lbd

    # If the most recent learned clauses are worse than the long-term average,
    # restart, as the solver is stuck in an unproductive search space. For this
    # the solver keeps two moving averages `ema_fast` and `ema_slow` and
    # checks if `ema_fast` is larger than `ema_slow` times some diff factor.
    # If so restart the search. This logic needs some kind of correction, as
    # the solver would otherwise restart instantly as `ema_fast` grows much
    # faster than `ema_slow` initially. This is implemented using a bias
    # correction, at the example of CaDiCaL, by dividing each ema by
    # `1 - (1 - α) ^ n`, where n is the number of conflicts.
    #
    def restart(self, lbd: int) -> None:
        self.conflicts_since_restart += 1

        self.biased_fast += ALPHA_FAST * (lbd - self.biased_fast)
        self.biased_slow += ALPHA_SLOW * (lbd - self.biased_slow)

        # this is `(1 - α) ^ n` implemented incrementaly
        self.exp_fast *= 1 - ALPHA_FAST
        self.exp_slow *= 1 - ALPHA_SLOW

        ema_fast = self.biased_fast / (1 - self.exp_fast)
        ema_slow = self.biased_slow / (1 - self.exp_slow)

        if (
            self.conflicts_since_restart >= RESTART_INT
            and ema_fast > RESTART_MARGIN * ema_slow
        ):
            self.cnf.backtrack(0)
            self.conflicts_since_restart = 0

    # If models already found, add blocking clause blocking all decisions made
    # on the way towards the model, forcing new decisions.
    #
    def block_model(self) -> bool:
        cnf = self.cnf

        # create blocking clause from the negated decision that lead to the
        # last model
        blocking = [-cnf.trail[start] for start in reversed(cnf.trail_starts)]

        # model was found on level 0, thus there is no other model
        if not blocking:
            return False

        # backtrack one level, add the blocking clause and assign the first
        # literal with its negated latest decision to force a new search space
        cnf.backtrack(len(cnf.trail_starts) - 1)
        cnf.add_asserting_clause(blocking)

        return True


if __name__ == "__main__":
    mysat = MySAT(sys.argv[1])

    solves = 3
    total_time = 0.0

    out = "outputs/out.csv"
    if len(sys.argv) > 2:
        out = sys.argv[2]

    f = open(out, "w")
    f.write("N, Status, Time (s), Total Time (s)\n")
    for i in range(1, solves + 1):
        start = time.perf_counter()
        ret = mysat.solve()
        end = time.perf_counter()
        solve_time = end - start
        total_time += solve_time
        f.write(f"{i}, {ret}, {solve_time:>.2}, {total_time:>.2}\n")

    f.close()
