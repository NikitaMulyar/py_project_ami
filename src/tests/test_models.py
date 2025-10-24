import os
import sys

import pytest
from datetime import datetime


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from src.library_management_system.models import Book, Member


def test_book_creation_valid(sample_book):
    assert sample_book.isbn == "978-0132350884"
    assert sample_book.title == "Clean Code"
    assert sample_book.available is True
    assert sample_book.borrowed_by is None


@pytest.mark.parametrize("isbn, title, author, year", [
    ("", "Title", "Author", 2000),                               # Пустой ISBN
    ("12345", "Title", "Author", 2000),                          # Короткий ISBN
    ("1234567890", "", "Author", 2000),                          # Пустое название
    ("1234567890", "Title", "", 2000),                           # Пустой автор
    ("1234567890", "Title", "Author", 999),                      # Невалидный год
    ("1234567890", "Title", "Author", datetime.now().year + 1),  # Год в будущем
])
def test_book_creation_invalid(isbn, title, author, year):
    with pytest.raises(ValueError):
        Book(isbn=isbn, title=title, author=author, year=year)


def test_book_borrow(sample_book):
    sample_book.borrow("M001", days=10)
    assert sample_book.available is False
    assert sample_book.borrowed_by == "M001"
    assert sample_book.due_date is not None
    assert sample_book.due_date > datetime.now()


def test_borrow_unavailable_book_raises_error(borrowed_book):
    with pytest.raises(RuntimeError, match="Книга уже выдана"):
        borrowed_book.borrow("M002")


def test_book_return(borrowed_book):
    borrowed_book.return_book()
    assert borrowed_book.available is True
    assert borrowed_book.borrowed_by is None
    assert borrowed_book.due_date is None


def test_return_available_book_raises_error(sample_book):
    with pytest.raises(RuntimeError, match="Книга не была выдана"):
        sample_book.return_book()


def test_is_overdue(overdue_book, borrowed_book):
    assert overdue_book.is_overdue() is True
    assert borrowed_book.is_overdue() is False
    book = Book("1234567890", "t", "a", 2000)
    assert book.is_overdue() is False


def test_book_serialization_cycle(sample_book):
    book_dict = sample_book.to_dict()
    new_book = Book.from_dict(book_dict)
    assert new_book == sample_book


def test_book_serialization_with_borrow_info(borrowed_book):
    book_dict = borrowed_book.to_dict()
    new_book = Book.from_dict(book_dict)
    assert new_book.isbn == borrowed_book.isbn
    assert new_book.borrowed_by == "M001"
    assert new_book.due_date.date() == borrowed_book.due_date.date()


def test_member_creation_valid(sample_member):
    assert sample_member.member_id == "M001"
    assert sample_member.name == "John Doe"
    assert sample_member.can_borrow() is True
    assert sample_member.borrowed_books == []


@pytest.mark.parametrize("member_id, name, email", [
    ("", "Name", "email@test.com"),     # Пустой ID
    ("M001", "", "email@test.com"),     # Пустое имя
    ("M001", "Name", "emailtest.com"),  # Невалидный email
])
def test_member_creation_invalid(member_id, name, email):
    with pytest.raises(ValueError):
        Member(member_id=member_id, name=name, email=email)


def test_member_can_borrow(sample_member, member_at_limit):
    assert sample_member.can_borrow() is True
    assert member_at_limit.can_borrow() is False


def test_add_borrowed_book(sample_member):
    sample_member.add_borrowed_book("ISBN1")
    assert sample_member.borrowed_books == ["ISBN1"]
    # Проверка на дубликаты
    sample_member.add_borrowed_book("ISBN1")
    assert sample_member.borrowed_books == ["ISBN1"]


def test_remove_borrowed_book(member_with_books):
    member_with_books.remove_borrowed_book("978-0134494166")
    assert "978-0134494166" not in member_with_books.borrowed_books
    # Удаление несуществующего ISBN не вызывает ошибку
    member_with_books.remove_borrowed_book("NON_EXISTENT_ISBN")
    assert len(member_with_books.borrowed_books) == 1


def test_member_serialization_cycle(sample_member):
    member_dict = sample_member.to_dict()
    new_member = Member.from_dict(member_dict)
    assert new_member == sample_member
