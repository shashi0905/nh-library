"""Domain exceptions for the library application."""


class LibraryException(Exception):
    """Base exception for all library domain exceptions."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        """Initialize exception with message and HTTP status code."""
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BookNotFound(LibraryException):
    """Exception raised when a book is not found."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("Book not found", status_code=404)


class MemberNotFound(LibraryException):
    """Exception raised when a member is not found."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("Member not found", status_code=404)


class LoanNotFound(LibraryException):
    """Exception raised when a loan is not found."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("Loan not found", status_code=404)


class BookNotAvailable(LibraryException):
    """Exception raised when a book has no available copies."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("Book is not available for borrowing", status_code=409)


class MemberInactive(LibraryException):
    """Exception raised when trying to borrow with an inactive member."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("Member account is inactive", status_code=403)


class LoanAlreadyReturned(LibraryException):
    """Exception raised when trying to return an already-returned loan."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("Loan has already been returned", status_code=409)


class DuplicateISBN(LibraryException):
    """Exception raised when ISBN already exists."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("ISBN already exists", status_code=409)


class DuplicateEmail(LibraryException):
    """Exception raised when email already exists."""

    def __init__(self) -> None:
        """Initialize with default message."""
        super().__init__("Email already exists", status_code=409)
