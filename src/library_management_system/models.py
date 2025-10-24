import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Type, TypeVar


TBook = TypeVar('TBook', bound='Book')
TMember = TypeVar('TMember', bound='Member')


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    year: int
    available: bool = True
    borrowed_by: Optional[str] = None
    due_date: Optional[datetime.datetime] = None

    def __post_init__(self):
        current_year = datetime.datetime.now().year
        if not self.isbn or len(self.isbn) < 10:
            raise ValueError("ISBN должен содержать не менее 10 символов.")
        if not self.title:
            raise ValueError("Название не может быть пустым.")
        if not self.author:
            raise ValueError("Автор не может быть пустым.")
        if not (1000 <= self.year <= current_year):
            raise ValueError(f"Год должен быть между 1000 и {current_year}.")

    def borrow(self, member_id: str, days: int = 14) -> None:
        if not self.available:
            raise RuntimeError("Книга уже выдана.")
        self.available = False
        self.borrowed_by = member_id
        self.due_date = datetime.datetime.now() + datetime.timedelta(days=days)

    def return_book(self) -> None:
        if self.available:
            raise RuntimeError("Книга не была выдана.")
        self.available = True
        self.borrowed_by = None
        self.due_date = None

    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        return datetime.datetime.now() > self.due_date

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "available": self.available,
            "borrowed_by": self.borrowed_by,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }
        return data

    @classmethod
    def from_dict(cls: Type[TBook], data: Dict[str, Any]) -> TBook:
        due_date = (
            datetime.datetime.fromisoformat(data["due_date"])
            if data.get("due_date")
            else None
        )
        return cls(
            isbn=data["isbn"],
            title=data["title"],
            author=data["author"],
            year=data["year"],
            available=data.get("available", True),
            borrowed_by=data.get("borrowed_by"),
            due_date=due_date,
        )


@dataclass
class Member:
    member_id: str
    name: str
    email: str
    borrowed_books: List[str] = field(default_factory=list)
    max_books: int = 3

    def __post_init__(self):
        if not self.member_id:
            raise ValueError("ID читателя не может быть пустым.")
        if not self.name:
            raise ValueError("Имя не может быть пустым.")
        if "@" not in self.email:
            raise ValueError("Email должен содержать символ '@'.")

    def can_borrow(self) -> bool:
        return len(self.borrowed_books) < self.max_books

    def add_borrowed_book(self, isbn: str) -> None:
        if isbn not in self.borrowed_books:
            self.borrowed_books.append(isbn)

    def remove_borrowed_book(self, isbn: str) -> None:
        if isbn in self.borrowed_books:
            self.borrowed_books.remove(isbn)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "name": self.name,
            "email": self.email,
            "borrowed_books": self.borrowed_books,
            "max_books": self.max_books,
        }

    @classmethod
    def from_dict(cls: Type[TMember], data: Dict[str, Any]) -> TMember:
        return cls(
            member_id=data["member_id"],
            name=data["name"],
            email=data["email"],
            borrowed_books=data.get("borrowed_books", []),
            max_books=data.get("max_books", 3),
        )
