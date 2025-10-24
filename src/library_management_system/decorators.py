import logging
import time
from functools import wraps
from typing import Callable, Any


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def log_operation(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Пропускаем self (первый аргумент)
        func_args = [repr(a) for a in args[1:]]
        func_kwargs = [f"{k}={v!r}" for k, v in kwargs.items()]
        arg_str = ", ".join(func_args + func_kwargs)
        
        logger.info(f"Вызов функции '{func.__name__}' с аргументами: {arg_str}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Функция '{func.__name__}' успешно завершилась.")
            return result
        except Exception as e:
            logger.error(f"Функция '{func.__name__}' вызвала исключение: {e}", exc_info=True)
            raise
    return wrapper


def measure_time(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Функция '{func.__name__}' выполнилась за {duration:.4f} секунд.")
        return result
    return wrapper


def validate_isbn(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        isbn = kwargs.get('isbn')
        if isbn is None:
            # Ищем isbn в позиционных аргументах (предполагаем, что это второй аргумент после self)
            if len(args) > 1:
                isbn = args[1]
        
        if not isinstance(isbn, str):
            raise ValueError("ISBN должен быть строкой.")
        if len(isbn) < 10:
            raise ValueError("ISBN должен содержать не менее 10 символов.")
            
        return func(*args, **kwargs)
    return wrapper


def require_member(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        member_id = kwargs.get('member_id')
        if member_id is None:
            # Ищем member_id в позиционных аргументах (предполагаем, что это третий аргумент)
            if len(args) > 2:
                member_id = args[2]

        if not member_id:
            raise ValueError("member_id is required")
            
        return func(*args, **kwargs)
    return wrapper
