class DatabaseException(Exception):
    pass


class NotFoundError(DatabaseException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(detail)


class HaveNoSessionError(DatabaseException):
    def __init__(self):
        super().__init__("Have no actual session")


class AlreadyExistsError(DatabaseException):
    def __init__(self, detail: str = "Record already exists"):
        super().__init__(detail)
