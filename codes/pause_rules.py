from abc import ABC, abstractmethod
from collections import Counter

class PauseRule(ABC):
    @abstractmethod
    def should_pause(self, ur_count, ur_names) -> bool:
        """Return True if reroll should pause"""
        pass

    def __repr__(self):
        return self.__class__.__name__


class MinURCountRule(PauseRule):
    def __init__(self, min_count):
        self.min_count = min_count

    def should_pause(self, ur_count, ur_names):
        return ur_count >= self.min_count

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_count})"


class ContainsAnyRule(PauseRule):
    def __init__(self, names):
        self.names = set(names)

    def should_pause(self, ur_count, ur_names):
        return any(name in self.names for name in ur_names)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.names})"


class ContainsAllRule(PauseRule):
    def __init__(self, names):
        self.required_counts = Counter(names)

    def should_pause(self, ur_count, ur_names):
        name_counts = Counter(ur_names)
        return all(name_counts[name] >= count for name, count in self.required_counts.items())

    def __repr__(self):
        return f"{self.__class__.__name__}({dict(self.required_counts)})"


class CompositeRule(PauseRule):
    def __init__(self, *rules):
        self.rules = rules

    def should_pause(self, ur_count, ur_names):
        return all(rule.should_pause(ur_count, ur_names) for rule in self.rules)

    def __repr__(self):
        return f"CompositeRule({', '.join(repr(r) for r in self.rules)})"
