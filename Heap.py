from typing import List


# MaxHeap for VSIDS variable decision heurisic. Each var has an acivity
# score, which is increased on conflicts, involving clauses including
# the var. On branching, the unassigned var with the highest activity is
# picked.
#
class Heap:
    def __init__(self, n_vars: int):
        self.activity: List[float] = [0.0] * (n_vars + 1)
        self.heap: List[int] = list(range(1, n_vars + 1))
        self.pos: List[int] = [-1] + list(range(n_vars))

        self.size: int = n_vars
        self.inc: float = 1.0

    # Seed activities with the number of occurrences of each var
    #
    def seed(self, clauses: List[List[int]]) -> None:
        for clause in clauses:
            for lit in clause:
                self.activity[abs(lit)] += 1.0

        for i in range(self.size // 2 - 1, -1, -1):
            self.sift_down(i)

    def parent(self, i: int) -> int:
        return (i - 1) // 2

    def left(self, i: int) -> int:
        return 2 * i + 1

    def right(self, i: int) -> int:
        return 2 * i + 2

    def insert(self, var: int) -> None:
        # no overwrite, if var already in heap
        if self.pos[var] != -1:
            return

        # append as leaf and sift up
        self.pos[var] = self.size
        self.heap.append(var)
        self.size += 1

        self.sift_up(self.pos[var])

    def swap(self, i: int, j: int) -> None:
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.pos[self.heap[i]], self.pos[self.heap[j]] = i, j

    def bump(self, clause: List[int]) -> None:
        for lit in clause:
            var = abs(lit)
            self.activity[var] += self.inc

            # only if var in heap, sift it up
            if self.pos[var] != -1:
                self.sift_up(self.pos[var])

            # prevent overflow of activity score into inf, by downscaling
            # everything
            if self.activity[var] > 1e100:
                self.activity = [a * 1e-100 for a in self.activity]
                self.inc *= 1e-100

        self.inc /= 0.95

    def sift_up(self, i: int) -> None:
        while i > 0:
            parent = self.parent(i)

            # if parent greater than child, then done
            if self.activity[self.heap[parent]] >= self.activity[self.heap[i]]:
                break

            # otherwise swap parent and child
            self.swap(i, parent)
            i = parent

    def sift_down(self, i: int) -> None:
        while True:
            left = self.left(i)
            right = self.right(i)
            largest = i

            # left child is greater? set it to largest
            if (
                left < self.size
                and self.activity[self.heap[left]] > self.activity[self.heap[largest]]
            ):
                largest = left

            # right child is greater? set it to largest
            if (
                right < self.size
                and self.activity[self.heap[right]] > self.activity[self.heap[largest]]
            ):
                largest = right

            # if parent is greatest, then done
            if largest == i:
                break

            # swap child with largest child
            self.swap(i, largest)
            i = largest

    def pop(self) -> int:
        if not self.heap:
            return 0

        top = self.heap[0]
        bottom = self.heap.pop()
        self.size -= 1
        self.pos[top] = -1

        # if top wasn't the only element
        if self.heap:
            self.heap[0] = bottom
            self.pos[bottom] = 0
            self.sift_down(0)

        return top
