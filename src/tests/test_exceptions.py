import os
import sys

import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from src.library_management_system.exceptions import *


def test_inheritance_hierarchy():
    assert issubclass(BookNotFoundError, LibraryException)
    assert issubclass(BookNotAvailableError, LibraryException)
    assert issubclass(MemberNotFoundError, LibraryException)
    assert issubclass(BorrowLimitExceededError, LibraryException)
    assert issubclass(InvalidDataError, LibraryException)


@pytest.mark.parametrize("exc_class, args, expected_attrs, expected_msg_part", [
    (BookNotFoundError, ("1234567890",), {"isbn": "1234567890"}, "Book with ISBN 1234567890 not found"),
    (BookNotAvailableError, ("0987654321",), {"isbn": "0987654321"}, "is not available for borrowing"),
    (MemberNotFoundError, ("M007",), {"member_id": "M007"}, "Member with ID M007 not found"),
    (BorrowLimitExceededError, ("M008", 3), {"member_id": "M008", "limit": 3}, "limit of 3 books"),
    (InvalidDataError, ("Test error message",), {}, "Test error message"),
])
def test_exception_attributes_and_message(exc_class, args, expected_attrs, expected_msg_part):
    with pytest.raises(exc_class) as exc_info:
        raise exc_class(*args)

    # Проверка сообщения
    assert expected_msg_part in str(exc_info.value)
    
    # Проверка атрибутов
    for attr, value in expected_attrs.items():
        assert getattr(exc_info.value, attr) == value


def test_catch_as_base_exception():
    try:
        raise BookNotFoundError("1234567890")
    except LibraryException as e:
        assert isinstance(e, BookNotFoundError)
    else:
        pytest.fail("Должно было быть вызвано исключение LibraryException")
