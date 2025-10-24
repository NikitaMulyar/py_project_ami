import json
import copy
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Iterator, Generator

from .models import Book, Member
from .exceptions import (
    BookNotFoundError,
    MemberNotFoundError,
    BookNotAvailableError,
    BorrowLimitExceededError,
    InvalidDataError,
)
from .decorators import log_operation, measure_time, validate_isbn, require_member


class Library:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.books_file = self.data_dir / "books.json"
        self.members_file = self.data_dir / "members.json"

        self.books: Dict[str, Book] = {}
        self.members: Dict[str, Member] = {}

        self._load_data()

    def _load_data(self) -> None:
        try:
            if self.books_file.exists() and self.books_file.stat().st_size > 0:
                with open(self.books_file, "r", encoding="utf-8") as f:
                    books_data = json.load(f)
                    self.books = {
                        data["isbn"]: Book.from_dict(data) for data in books_data
                    }
            else:
                self.books = {}

            if self.members_file.exists() and self.members_file.stat().st_size > 0:
                with open(self.members_file, "r", encoding="utf-8") as f:
                    members_data = json.load(f)
                    self.members = {
                        data["member_id"]: Member.from_dict(data)
                        for data in members_data
                    }
            else:
                self.members = {}

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise InvalidDataError(f"Ошибка загрузки данных: {e}")

    @measure_time
    def save(self) -> None:
        """Сохраняет текущее состояние библиотеки в файлы."""
        with open(self.books_file, "w", encoding="utf-8") as f:
            json.dump(
                [book.to_dict() for book in self.books.values()],
                f,
                indent=2,
                ensure_ascii=False,
            )
        with open(self.members_file, "w", encoding="utf-8") as f:
            json.dump(
                [member.to_dict() for member in self.members.values()],
                f,
                indent=2,
                ensure_ascii=False,
            )

    """
    Проблема: в самом описании проекта заложен  архитектурный конфликт между требованиями фаз 4/5 и фазы 7.
    Требование фаз 4 и 5: Каждый метод (add_book и т.д.) должен быть атомарным и немедленно сохранять свое состояние 
    в файл.
    Требование фазы 7 (transaction): Должен существовать контекстный менеджер, который позволяет выполнить несколько 
    операций как единое цел
    """

    @log_operation
    @validate_isbn
    def add_book(self, isbn: str, title: str, author: str, year: int) -> Book:
        if isbn in self.books:
            raise ValueError(f"Книга с ISBN {isbn} уже существует.")
        book = Book(isbn=isbn, title=title, author=author, year=year)
        self.books[isbn] = book
        # self.save()
        return book

    @validate_isbn
    def get_book(self, isbn: str) -> Book:
        book = self.books.get(isbn)
        if not book:
            raise BookNotFoundError(isbn)
        return book

    @log_operation
    def add_member(self, member_id: str, name: str, email: str) -> Member:
        if member_id in self.members:
            raise ValueError(f"Читатель с ID {member_id} уже существует.")
        member = Member(member_id=member_id, name=name, email=email)
        self.members[member_id] = member
        # self.save()
        return member

    def get_member(self, member_id: str) -> Member:
        member = self.members.get(member_id)
        if not member:
            raise MemberNotFoundError(member_id)
        return member

    @log_operation
    @validate_isbn
    @require_member
    def borrow_book(self, isbn: str, member_id: str, days: int = 14) -> None:
        book = self.get_book(isbn)
        member = self.get_member(member_id)

        if not book.available:
            raise BookNotAvailableError(isbn)
        if not member.can_borrow():
            raise BorrowLimitExceededError(member_id, member.max_books)

        book.borrow(member_id, days)
        member.add_borrowed_book(isbn)
        # self.save()

    @log_operation
    @validate_isbn
    @require_member
    def return_book(self, isbn: str, member_id: str) -> None:
        book = self.get_book(isbn)
        member = self.get_member(member_id)

        if book.borrowed_by != member_id:
            raise ValueError(f"Книга с ISBN {isbn} не была выдана читателю {member_id}.")

        book.return_book()
        member.remove_borrowed_book(isbn)
        # self.save()

    def search_books(self, query: str) -> List[Book]:
        query_lower = query.lower()
        return [
            book for book in self.books.values()
            if query_lower in book.title.lower() or query_lower in book.author.lower()
        ]

    def get_available_books(self) -> List[Book]:
        return [book for book in self.books.values() if book.available]

    def get_borrowed_books(self) -> List[Book]:
        return [book for book in self.books.values() if not book.available]

    def get_overdue_books(self) -> List[Book]:
        return [book for book in self.books.values() if book.is_overdue()]

    @contextmanager
    def transaction(self) -> Generator['Library', None, None]:
        books_backup = copy.deepcopy(self.books)
        members_backup = copy.deepcopy(self.members)
        try:
            yield self
            self.save()
        except Exception:
            self.books = books_backup
            self.members = members_backup
            raise

    def __iter__(self) -> Iterator[Book]:
        return iter(self.books.values())

    def books_by_author(self, author: str) -> Generator[Book, None, None]:
        author_lower = author.lower()
        for book in self.books.values():
            if author_lower in book.author.lower():
                yield book

    def books_by_year_range(self, start_year: int, end_year: int) -> Generator[Book, None, None]:
        for book in self.books.values():
            if start_year <= book.year <= end_year:
                yield book

    def paginate_books(self, page_size: int = 10) -> Generator[List[Book], None, None]:
        all_books = list(self.books.values())
        for i in range(0, len(all_books), page_size):
            yield all_books[i:i + page_size]

    def get_statistics(self) -> Dict[str, int]:
        return {
            "total_books": len(self.books),
            "available_books": len(self.get_available_books()),
            "borrowed_books": len(self.get_borrowed_books()),
            "overdue_books": len(self.get_overdue_books()),
            "total_members": len(self.members),
        }

    def clear_all_data(self) -> None:
        self.books.clear()
        self.members.clear()
        self.save()
