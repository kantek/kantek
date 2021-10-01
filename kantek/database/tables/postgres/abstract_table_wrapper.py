import abc

from asyncpg import Pool


class AbstractTableWrapper(abc.ABC):
    def __init__(self, pool):
        self.pool: Pool = pool
