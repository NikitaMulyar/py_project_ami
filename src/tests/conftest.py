import os
import sys

import pytest
import tempfile
import shutil
import datetime


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from src.library_management_system.library import Library
from src.library_management_system.models import Book, Member


@pytest.fixture(scope="function")
def temp_dir():
    """Создает временную директорию для тестов."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture(scope="function")
def library(temp_dir):
    """Создает свежий экземпляр Library для каждого теста."""
    return Library(data_dir=temp_dir)


@pytest.fixture
def sample_book():
    return Book(
        isbn="978-0132350884",
        title="Clean Code",
        author="Robert C. Martin",
        year=2008,
    )


@pytest.fixture
def sample_member():
    return Member(member_id="M001", name="John Doe", email="john.doe@example.com")


@pytest.fixture(scope="function")
def populated_library(library: Library):
    """Возвращает библиотеку с несколькими книгами и читателями для КАЖДОГО теста."""
    library.add_book("978-0132350884", "Clean Code", "Robert C. Martin", 2008)
    library.add_book("978-0201633610", "Design Patterns", "Erich Gamma", 1994)
    library.add_book("978-0735619678", "Code Complete", "Steve McConnell", 2004)
    library.add_book("978-0134494166", "Effective Python", "Brett Slatkin", 2019)
    library.add_book("978-1491904244", "Fluent Python", "Luciano Ramalho", 2015)

    library.add_member("M001", "John Doe", "john@example.com")
    library.add_member("M002", "Jane Smith", "jane@example.com")
    library.add_member("M003", "Peter Jones", "peter@example.com")

    library.save()

    return library


@pytest.fixture
def borrowed_book():
    book = Book(
        isbn="978-0201633610",
        title="Design Patterns",
        author="Erich Gamma",
        year=1994,
        available=False,
        borrowed_by="M001",
        due_date=datetime.datetime.now() + datetime.timedelta(days=10),
    )
    return book


@pytest.fixture
def overdue_book():
    book = Book(
        isbn="978-1593275846",
        title="Automate the Boring Stuff with Python",
        author="Al Sweigart",
        year=2015,
        available=False,
        borrowed_by="M002",
        due_date=datetime.datetime.now() - datetime.timedelta(days=5),
    )
    return book


@pytest.fixture
def member_with_books():
    member = Member(
        member_id="M002",
        name="Jane Smith",
        email="jane@example.com",
        borrowed_books=["978-0735619678", "978-0134494166"],
    )
    return member


@pytest.fixture
def member_at_limit():
    member = Member(
        member_id="M003",
        name="Peter Jones",
        email="peter@example.com",
        borrowed_books=["1", "2", "3"],
        max_books=3,
    )
    return member
