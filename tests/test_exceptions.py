import pytest

from metaorm import (
    AlreadyExistsError,
    DatabaseException,
    HaveNoSessionError,
    NotFoundError,
)


class TestExceptions:
    def test_database_exception_is_base_class(self) -> None:
        assert issubclass(NotFoundError, DatabaseException)
        assert issubclass(HaveNoSessionError, DatabaseException)
        assert issubclass(AlreadyExistsError, DatabaseException)

    def test_not_found_error_default_message(self) -> None:
        error = NotFoundError()

        assert str(error) == "Not found"

    def test_not_found_error_custom_message(self) -> None:
        error = NotFoundError(detail="User not found")

        assert str(error) == "User not found"

    def test_have_no_session_error_message(self) -> None:
        error = HaveNoSessionError()

        assert str(error) == "Have no actual session"

    def test_already_exists_error_default_message(self) -> None:
        error = AlreadyExistsError()

        assert str(error) == "Record already exists"

    def test_already_exists_error_custom_message(self) -> None:
        error = AlreadyExistsError(detail="User already exists")

        assert str(error) == "User already exists"

    @pytest.mark.parametrize(
        "exception_class",
        [
            DatabaseException,
            NotFoundError,
            HaveNoSessionError,
            AlreadyExistsError,
        ],
    )
    def test_all_exceptions_are_catchable_as_database_exception(
        self,
        exception_class: type[Exception],
    ) -> None:
        with pytest.raises(DatabaseException):
            raise exception_class()
