import arcadedb_embedded as arcadedb


class DatabaseConnection:
    def __init__(self, database: arcadedb.Database) -> None:
        self._database = database

    @property
    def database(self) -> arcadedb.Database:
        return self._database
