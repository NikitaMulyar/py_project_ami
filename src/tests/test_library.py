import os
import sys

import pytest
import json
from pathlib import Path


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from src.library_management_system.library import Library
from src.library_management_system.exceptions import *


class TestLibraryInitialization:
    def test_creates_data_dir(self, temp_dir):
        dir_path = Path(temp_dir)
        Library(data_dir=str(dir_path))
        assert dir_path.exists()

    def test_initializes_empty(self, library):
        assert library.books == {}
        assert library.members == {}

    def test_loads_existing_data(self, temp_dir):
        books_data = [{"isbn": "1234567890", "title": "t", "author": "a", "year": 2000}]
        members_data = [{"member_id": "M1", "name": "n", "email": "e@e.com"}]

        data_path = Path(temp_dir)
        (data_path / "books.json").write_text(json.dumps(books_data), encoding='utf-8')
        (data_path / "members.json").write_text(json.dumps(members_data), encoding='utf-8')

        lib = Library(data_dir=temp_dir)
        assert "1234567890" in lib.books
        assert "M1" in lib.members

    def test_raises_for_corrupted_json(self, temp_dir):
        data_path = Path(temp_dir)
        (data_path / "books.json").write_text("this is not json", encoding='utf-8')

        with pytest.raises(InvalidDataError):
            Library(data_dir=temp_dir)

    def test_handles_empty_json_file(self, temp_dir):
        data_path = Path(temp_dir)
        (data_path / "books.json").touch()
        lib = Library(data_dir=temp_dir)
        assert not lib.books


class TestBookOperations:
    def test_add_book_success(self, library):
        library.add_book("1234567890", "Test Book", "Test Author", 2021)
        # Изменение только в памяти, пока не вызван save()
        assert "1234567890" in library.books

        library.save()  # Явно сохраняем

        new_lib = Library(data_dir=library.data_dir)
        assert "1234567890" in new_lib.books

    def test_add_duplicate_book_fails(self, populated_library):
        with pytest.raises(ValueError, match="уже существует"):
            populated_library.add_book("978-0132350884", "Clean Code", "Robert C. Martin", 2008)

    def test_get_book_success(self, populated_library):
        book = populated_library.get_book("978-0132350884")
        assert book.title == "Clean Code"

    def test_get_nonexistent_book_fails(self, library):
        with pytest.raises(BookNotFoundError):
            library.get_book("000-0000000000")


class TestMemberOperations:
    def test_add_member_success(self, library):
        library.add_member("M99", "Test Member", "test@test.com")
        library.save()

        new_lib = Library(data_dir=library.data_dir)
        assert "M99" in new_lib.members
        assert new_lib.members["M99"].name == "Test Member"

    def test_add_duplicate_member_fails(self, populated_library):
        with pytest.raises(ValueError, match="уже существует"):
            populated_library.add_member("M001", "John Doe", "john@example.com")

    def test_get_member_success(self, populated_library):
        member = populated_library.get_member("M001")
        assert member.name == "John Doe"

    def test_get_nonexistent_member_fails(self, library):
        with pytest.raises(MemberNotFoundError):
            library.get_member("M-NON-EXIST")


class TestBorrowReturnOperations:
    def test_borrow_book_success(self, populated_library):
        isbn = "978-0132350884"
        member_id = "M001"
        populated_library.borrow_book(isbn, member_id)
        populated_library.save()

        book = populated_library.get_book(isbn)
        member = populated_library.get_member(member_id)
        assert not book.available
        assert isbn in member.borrowed_books

        reloaded_lib = Library(data_dir=populated_library.data_dir)
        assert not reloaded_lib.get_book(isbn).available

    def test_borrow_unavailable_book_fails(self, populated_library):
        isbn = "978-0132350884"
        populated_library.borrow_book(isbn, "M001")
        with pytest.raises(BookNotAvailableError):
            populated_library.borrow_book(isbn, "M002")

    def test_borrow_at_limit_fails(self, populated_library, member_at_limit):
        populated_library.members[member_at_limit.member_id] = member_at_limit
        with pytest.raises(BorrowLimitExceededError):
            populated_library.borrow_book("978-0132350884", member_at_limit.member_id)

    def test_return_book_success(self, populated_library):
        isbn = "978-0132350884"
        member_id = "M001"
        populated_library.borrow_book(isbn, member_id)
        populated_library.save()

        populated_library.return_book(isbn, member_id)
        populated_library.save()

        book = populated_library.get_book(isbn)
        member = populated_library.get_member(member_id)
        assert book.available
        assert isbn not in member.borrowed_books


class TestSearchAndFilter:
    # Эти тесты не изменяют состояние, поэтому остаются без изменений
    def test_search_books_by_title(self, populated_library):
        results = populated_library.search_books("python")
        assert len(results) == 2

    def test_search_books_by_author(self, populated_library):
        results = populated_library.search_books("martin")
        assert len(results) == 1

    def test_get_available_books(self, populated_library):
        populated_library.borrow_book("978-0132350884", "M001")
        available = populated_library.get_available_books()
        assert len(available) == 4

    def test_get_borrowed_books(self, populated_library):
        populated_library.borrow_book("978-0132350884", "M001")
        borrowed = populated_library.get_borrowed_books()
        assert len(borrowed) == 1
        assert borrowed[0].isbn == "978-0132350884"

    def test_get_overdue_books(self, populated_library, overdue_book):
        populated_library.books[overdue_book.isbn] = overdue_book
        overdue = populated_library.get_overdue_books()
        assert len(overdue) == 1
        assert overdue[0].isbn == overdue_book.isbn


class TestAdvancedFeatures:
    def test_context_manager_success(self, library):
        with library.transaction() as tx:
            tx.add_book("1234567890", "t", "a", 2000)
            tx.add_member("M1", "n", "e@e.com")

        new_lib = Library(data_dir=library.data_dir)
        assert "1234567890" in new_lib.books
        assert "M1" in new_lib.members

    def test_context_manager_failure_restores_state(self, populated_library):
        original_book_count = len(populated_library.books)

        with pytest.raises(ValueError, match="Something went wrong"):
            with populated_library.transaction() as tx:
                tx.add_book("new-isbn-123", "New Book", "New Author", 2023)
                # Это изменение теперь происходит только в памяти
                assert len(tx.books) == original_book_count + 1
                raise ValueError("Something went wrong")

        # Проверяем, что состояние в памяти откатилось
        assert len(populated_library.books) == original_book_count
        assert "new-isbn-123" not in populated_library.books

        # Проверяем, что состояние в файле не изменилось
        reloaded_lib = Library(data_dir=populated_library.data_dir)
        assert len(reloaded_lib.books) == original_book_count

    def test_get_statistics(self, populated_library, overdue_book):
        assert populated_library.get_statistics()["total_books"] == 5

        populated_library.borrow_book("978-0132350884", "M001")

        # Добавляем просроченную книгу
        populated_library.books[overdue_book.isbn] = overdue_book

        stats = populated_library.get_statistics()

        assert stats["total_books"] == 6
        assert stats["available_books"] == 4
        assert stats["borrowed_books"] == 2
        assert stats["overdue_books"] == 1
        assert stats["total_members"] == 3
