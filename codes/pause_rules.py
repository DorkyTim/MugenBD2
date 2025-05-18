from abc import ABC, abstractmethod

class PauseRule(ABC):
    @abstractmethod
    def should_pause(self, ur_count, ur_names):
        """Return True if reroll should pause"""
        pass


class URCountRule(PauseRule):
    def __init__(self, min_count):
        self.min_count = min_count

    def should_pause(self, ur_count, ur_names):
        return ur_count >= self.min_count


class ContainsAnyRule(PauseRule):
    def __init__(self, names):
        self.names = set(names)

    def should_pause(self, ur_count, ur_names):
        return any(name in self.names for name in ur_names)


class ContainsAllRule(PauseRule):
    def __init__(self, names):
        self.names = set(names)

    def should_pause(self, ur_count, ur_names):
        return self.names.issubset(set(ur_names))
