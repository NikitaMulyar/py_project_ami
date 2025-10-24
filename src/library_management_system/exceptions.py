class LibraryException(Exception):
    """Базовое исключение для ошибок в библиотеке."""
    pass


class BookNotFoundError(LibraryException):
    def __init__(self, isbn: str):
        self.isbn = isbn
        super().__init__(f"Book with ISBN {isbn} not found")


class BookNotAvailableError(LibraryException):
    def __init__(self, isbn: str):
        self.isbn = isbn
        super().__init__(f"Book with ISBN {isbn} is not available for borrowing")


class MemberNotFoundError(LibraryException):
    def __init__(self, member_id: str):
        self.member_id = member_id
        super().__init__(f"Member with ID {member_id} not found")


class BorrowLimitExceededError(LibraryException):
    def __init__(self, member_id: str, limit: int):
        self.member_id = member_id
        self.limit = limit
        super().__init__(f"Member {member_id} has reached the borrowing limit of {limit} books")


class InvalidDataError(LibraryException):
    def __init__(self, message: str):
        super().__init__(message)
