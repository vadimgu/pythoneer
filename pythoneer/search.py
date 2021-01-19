from typing import Iterable


class Testable:
    pass


class Search:
    def __init__(self, programmer: Iterable[Testable], optimization_objective: str):
        self.programmer = programmer
        self.optimization_objective = optimization_objective

    def fetch_all(self):
        ...

    def fetch_partials(self):
        ...

    def fetch_complete(self):
        ...

    def fetch_one(self):
        ...
