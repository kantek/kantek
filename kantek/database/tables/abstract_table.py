import abc


class AbstractTable(abc.ABC):
    def __init__(self, parent: 'Database'):
        self.db = parent.db
