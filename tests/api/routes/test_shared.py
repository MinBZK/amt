import asyncio
import contextlib
import threading
from dataclasses import dataclass
from typing import Any, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from amt.api.routes.shared import (
    replace_none_with_empty_string_inplace,
    run_async_function,  # pyright: ignore[reportUnknownVariableType]
)
from amt.schema.shared import IterMixin


def test_replace_none_with_empty_string_inplace() -> None:
    @dataclass
    class TestClass2(IterMixin):
        test_class_obj: list[str | None] | None = None
        test_list: list[list[str | None] | None] | None = None

    @dataclass
    class TestClass(IterMixin):
        test_list: list[str | None] | None = None
        test_dict: dict[str, str | None] | None = None
        test_itermixin: IterMixin | None = None
        test_str: str | None = None

    my_obj = TestClass(
        test_list=[None],
        test_dict={"key": None, "key2": "value2"},
        test_itermixin=TestClass2(test_class_obj=[None], test_list=[["a"], ["b"], [None]]),
        test_str=None,
    )

    replace_none_with_empty_string_inplace(my_obj)

    assert my_obj.test_list == [""]
    assert my_obj.test_dict == {"key": "", "key2": "value2"}
    assert my_obj.test_str == ""
    assert my_obj.test_itermixin.test_class_obj == [""]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportOptionalMemberAccess]
    assert my_obj.test_itermixin.test_list == [["a"], ["b"], [""]]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportOptionalMemberAccess]


T = TypeVar("T")


# Test async functions to be used in tests
async def async_return_value(value: T) -> T:
    """Simple async function that returns a value."""
    return value


async def async_raise_exception() -> None:
    """Async function that raises an exception."""
    raise ValueError("Test exception")


async def async_sleep_and_return(sleep_time: float, value: T) -> T:
    """Async function that sleeps and then returns a value."""
    await asyncio.sleep(sleep_time)
    return value


def test_no_event_loop() -> None:
    """Test when no event loop is running."""
    # This is the default case when running a test
    assert run_async_function(async_return_value, "test_value") == "test_value"


def test_no_event_loop_exception() -> None:
    """Test when no event loop is running and the async function raises an exception."""
    # In this case, the exception should be propagated correctly
    with pytest.raises(ValueError, match="Test exception"):
        run_async_function(async_raise_exception)


def test_runtime_error_handling() -> None:
    """Test when asyncio.get_running_loop raises RuntimeError."""
    # Mock get_running_loop to raise RuntimeError and asyncio.run to return a value
    with (
        patch("asyncio.get_running_loop", side_effect=RuntimeError("No running event loop")),
        patch("asyncio.run", return_value="fallback_value"),
    ):
        assert run_async_function(async_return_value, "any_value") == "fallback_value"


@pytest.mark.asyncio
async def test_event_loop_in_main_thread() -> None:
    """Test when an event loop is running in the main thread."""
    # Create a task that keeps the loop busy
    task = asyncio.create_task(asyncio.sleep(1))

    # The event loop is now running in this test
    # Define a function to run our test function
    test_result: str | None = None

    def run_test() -> None:
        nonlocal test_result
        test_result = run_async_function(async_return_value, "main_thread_value")  # pyright: ignore[reportUnknownVariableType]

    test_thread = threading.Thread(target=run_test)
    test_thread.start()
    test_thread.join(timeout=1.0)

    # Clean up
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert test_result == "main_thread_value"


@pytest.mark.asyncio
async def test_event_loop_in_main_thread_exception() -> None:
    """Test when an event loop is running in the main thread and function raises an exception."""
    # Create a task that keeps the loop busy
    task = asyncio.create_task(asyncio.sleep(1))

    # The event loop is now running in this test
    # Define a function to run our test function
    exception_raised = False

    def run_test_with_exception() -> None:
        nonlocal exception_raised
        try:
            run_async_function(async_raise_exception)
        except ValueError as e:
            if str(e) == "Test exception":
                exception_raised = True

    test_thread = threading.Thread(target=run_test_with_exception)
    test_thread.start()
    test_thread.join(timeout=1.0)

    # Clean up
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert exception_raised, "Exception was not properly propagated from thread with running event loop"


def test_event_loop_in_different_thread() -> None:
    """Test when an event loop is running in a different thread but function is called from another thread."""
    # Create a mock thread object that is not the main thread
    mock_thread = MagicMock()
    mock_loop = MagicMock()
    mock_loop.is_running.return_value = True

    # Mock all relevant functions in a single with statement
    with (
        patch("threading.current_thread", return_value=mock_thread),
        patch("threading.main_thread", return_value=MagicMock()),
        patch("asyncio.get_running_loop", return_value=mock_loop),
        patch("asyncio.run", return_value="different_thread_value"),
    ):
        assert run_async_function(async_return_value, "different_thread_value") == "different_thread_value"


def test_event_loop_in_different_thread_exception() -> None:
    """Test when an event loop is running in a different thread and async function raises an exception."""
    # Create a mock thread object that is not the main thread
    mock_thread = MagicMock()
    mock_loop = MagicMock()
    mock_loop.is_running.return_value = True
    test_exception = ValueError("Test exception from different thread")

    # Mock all relevant functions in a single with statement
    with (
        patch("threading.current_thread", return_value=mock_thread),
        patch("threading.main_thread", return_value=MagicMock()),
        patch("asyncio.get_running_loop", return_value=mock_loop),
        patch("asyncio.run", side_effect=test_exception),
        pytest.raises(ValueError, match="Test exception from different thread"),
    ):
        run_async_function(async_raise_exception)


def test_function_raises_exception() -> None:
    """Test when the async function raises an exception."""
    with pytest.raises(ValueError, match="Test exception"):
        run_async_function(async_raise_exception)


def test_exception_in_thread() -> None:
    """Test when the async function raises an exception in a thread."""
    # Setup a task with a function that will raise an exception
    exception_raised = False

    def run_test_with_exception() -> None:
        nonlocal exception_raised
        try:
            run_async_function(async_raise_exception)
        except ValueError as e:
            if str(e) == "Test exception":
                exception_raised = True

    # Run in a thread
    test_thread = threading.Thread(target=run_test_with_exception)
    test_thread.start()
    test_thread.join(timeout=1.0)

    assert exception_raised, "Exception was not properly propagated from thread"


@pytest.mark.asyncio
async def test_function_with_args_kwargs() -> None:
    """Test with positional and keyword arguments."""

    async def async_args_kwargs(*args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:  # noqa ANN401
        return args, kwargs

    assert run_async_function(async_args_kwargs, 1, 2, a="a", b="b") == ((1, 2), {"a": "a", "b": "b"})


@pytest.mark.asyncio
async def test_complex_data_structures() -> None:
    """Test with complex data structures."""
    test_data: dict[str, Any] = {"list": [1, 2, 3], "dict": {"a": 1, "b": 2}, "tuple": (1, 2, 3)}
    assert run_async_function(async_return_value, test_data) == test_data


@pytest.mark.asyncio
async def test_nested_async_functions() -> None:
    """Test with nested async functions."""

    async def outer_async() -> str:
        inner_result = await async_return_value("inner")
        return f"outer_{inner_result}"

    assert run_async_function(outer_async) == "outer_inner"


@pytest.mark.asyncio
async def test_long_running_async_task() -> None:
    """Test with a long-running async task."""
    assert run_async_function(async_sleep_and_return, 0.5, "delayed_result") == "delayed_result"
