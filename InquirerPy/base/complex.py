"""Contains the interface class :class:`.BaseComplexPrompt` for more complex prompts and the mocked document class :class:`.FakeDocument`."""
import shutil
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple, Union

from prompt_toolkit.application import Application
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.filters.base import Condition, FilterOrBool
from prompt_toolkit.key_binding.key_bindings import KeyHandlerCallable
from prompt_toolkit.keys import Keys

from InquirerPy.base.simple import BaseSimplePrompt
from InquirerPy.enum import INQUIRERPY_KEYBOARD_INTERRUPT
from InquirerPy.utils import (
    InquirerPySessionResult,
    InquirerPyStyle,
    InquirerPyValidate,
)


@dataclass
class FakeDocument:
    """A fake `prompt_toolkit` document class.

    Work around to allow non-buffer type :class:`~prompt_toolkit.layout.UIControl` to use
    :class:`~prompt_toolkit.validation.Validator`.

    Args:
        text: Content to be validated.
        cursor_position: Fake cursor position.
    """

    text: str
    cursor_position: int = 0


class BaseComplexPrompt(BaseSimplePrompt):
    """A base class to create a more complex prompt that will involve :class:`~prompt_toolkit.application.Application`.

    Note:
        This class does not create :class:`~prompt_toolkit.layout.Layout` nor :class:`~prompt_toolkit.application.Application`,
        it only contains the necessary attributes and helper functions to be consumed.

    Note:
        Use :class:`~InquirerPy.base.BaseListPrompt` to create a complex list prompt which involves multiple choices. It has
        more methods and helper function implemented.

    See Also:
        :class:`~InquirerPy.base.BaseListPrompt`
        :class:`~InquirerPy.prompts.fuzzy.FuzzyPrompt`
    """

    def __init__(
        self,
        message: Union[str, Callable[[InquirerPySessionResult], str]],
        style: Optional[InquirerPyStyle] = None,
        border: bool = False,
        vi_mode: bool = False,
        qmark: str = "?",
        amark: str = "?",
        instruction: str = "",
        long_instruction: str = "",
        transformer: Optional[Callable[[Any], Any]] = None,
        filter: Optional[Callable[[Any], Any]] = None,
        validate: Optional[InquirerPyValidate] = None,
        invalid_message: str = "Invalid input",
        wrap_lines: bool = True,
        raise_keyboard_interrupt: bool = True,
        mandatory: bool = True,
        mandatory_message: str = "Mandatory prompt",
        session_result: Optional[InquirerPySessionResult] = None,
    ) -> None:
        super().__init__(
            message=message,
            style=style,
            vi_mode=vi_mode,
            qmark=qmark,
            amark=amark,
            instruction=instruction,
            transformer=transformer,
            filter=filter,
            invalid_message=invalid_message,
            validate=validate,
            wrap_lines=wrap_lines,
            raise_keyboard_interrupt=raise_keyboard_interrupt,
            mandatory=mandatory,
            mandatory_message=mandatory_message,
            session_result=session_result,
        )
        self._invalid_message = invalid_message
        self._rendered = False
        self._invalid = False
        self._loading = False
        self._application: Application
        self._long_instruction = long_instruction
        self._border = border
        self._height_offset = 2  # prev prompt result + current prompt question
        if self._border:
            self._height_offset += 2
        if self._long_instruction:
            self._height_offset += 1
        self._validation_window_bottom_offset = 0 if not self._long_instruction else 1
        if self._wrap_lines:
            self._validation_window_bottom_offset += (
                self.extra_long_instruction_line_count
            )

        self._is_vim_edit = Condition(lambda: self._editing_mode == EditingMode.VI)
        self._is_invalid = Condition(lambda: self._invalid)
        self._is_displaying_long_instruction = Condition(
            lambda: self._long_instruction != ""
        )

    def _redraw(self) -> None:
        """Redraw the application UI."""
        pass

    def register_kb(
        self, *keys: Union[Keys, str], filter: FilterOrBool = True
    ) -> Callable[[KeyHandlerCallable], KeyHandlerCallable]:
        """Decorate keybinding registration function.

        Ensure that the `invalid` state is cleared on next keybinding entered.
        """
        pass

    def _exception_handler(self, _, context) -> None:
        """Set exception handler for the event loop.

        Skip the question and raise exception.

        Args:
            loop: Current event loop.
            context: Exception context.
        """
        pass

    def _after_render(self, app: Optional[Application]) -> None:
        """Run after the :class:`~prompt_toolkit.application.Application` is rendered/updated.

        Since this function is fired up on each render, adding a check on `self._rendered` to
        process logics that should only run once.

        Set event loop exception handler here, since its guaranteed that the event loop is running
        in `_after_render`.
        """
        pass

    def _set_error(self, message: str) -> None:
        """Set error message and set invalid state.

        Args:
            message: Error message to display.
        """
        pass

    def _get_error_message(self) -> List[Tuple[str, str]]:
        """Obtain the error message dynamically.

        Returns:
            FormattedText in list of tuple format.
        """
        pass

    def _on_rendered(self, _: Optional[Application]) -> None:
        """Run once after the UI is rendered. Acts like `ComponentDidMount`."""
        pass

    def _get_prompt_message(self) -> List[Tuple[str, str]]:
        """Get the prompt message to display.

        Returns:
            Formatted text in list of tuple format.
        """
        pass

    def _run(self) -> Any:
        """Run the application."""
        pass

    async def _run_async(self) -> None:
        """Run the application asynchronously."""
        pass

    @property
    def application(self) -> Application:
        """Get the application.

        :class:`.BaseComplexPrompt` requires :attr:`.BaseComplexPrompt._application` to be defined since this class
        doesn't implement :class:`~prompt_toolkit.layout.Layout` and :class:`~prompt_toolkit.application.Application`.

        Raises:
            NotImplementedError: When `self._application` is not defined.
        """
        pass

    @application.setter
    def application(self, value: Application) -> None:
        pass

    @property
    def height_offset(self) -> int:
        """int: Height offset to apply."""
        pass

    @property
    def total_message_length(self) -> int:
        """int: Total length of the message."""
        pass

    @property
    def extra_message_line_count(self) -> int:
        """int: Get the extra lines created caused by line wrapping.

        Minus 1 on the totoal message length as we only want the extra line.
        24 // 24 will equal to 1 however we only want the value to be 1 when we have 25 char
        which will create an extra line.
        """
        pass

    @property
    def extra_long_instruction_line_count(self) -> int:
        """int: Get the extra lines created caused by line wrapping.

        See Also:
            :attr:`.BaseComplexPrompt.extra_message_line_count`
        """
        pass

    @property
    def extra_line_count(self) -> int:
        """Get the extra lines created caused by line wrapping.

        Used mainly to calculate how much additional offset should be applied when getting
        the height.

        Returns:
            Total extra lines created due to line wrapping.
        """
        pass
