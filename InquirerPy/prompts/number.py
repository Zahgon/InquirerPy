"""Module contains the class to create a number prompt."""
import re
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union, cast

from prompt_toolkit.application.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters.base import Condition
from prompt_toolkit.filters.cli import IsDone
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HorizontalAlign,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import (
    BufferControl,
    DummyControl,
    FormattedTextControl,
)
from prompt_toolkit.layout.dimension import Dimension, LayoutDimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.lexers.base import SimpleLexer
from prompt_toolkit.validation import ValidationError

from InquirerPy.base.complex import BaseComplexPrompt, FakeDocument
from InquirerPy.containers.instruction import InstructionWindow
from InquirerPy.containers.validation import ValidationWindow
from InquirerPy.enum import INQUIRERPY_QMARK_SEQUENCE
from InquirerPy.exceptions import InvalidArgument
from InquirerPy.utils import (
    InquirerPyDefault,
    InquirerPyKeybindings,
    InquirerPyMessage,
    InquirerPySessionResult,
    InquirerPyStyle,
    InquirerPyValidate,
)

if TYPE_CHECKING:
    from prompt_toolkit.key_binding.key_processor import KeyPressEvent

__all__ = ["NumberPrompt"]


class NumberPrompt(BaseComplexPrompt):
    """Create a input prompts that only takes number as input.

    A wrapper class around :class:`~prompt_toolkit.application.Application`.

    Args:
        message: The question to ask the user.
            Refer to :ref:`pages/dynamic:message` documentation for more details.
        style: An :class:`InquirerPyStyle` instance.
            Refer to :ref:`Style <pages/style:Alternate Syntax>` documentation for more details.
        vi_mode: Use vim keybinding for the prompt.
            Refer to :ref:`pages/kb:Keybindings` documentation for more details.
        default: Set the default value of the prompt.
            You can enter either the floating value or integer value as the default.
            Refer to :ref:`pages/dynamic:default` documentation for more details.
        float_allowed: Allow decimal input. This will change the prompt to have 2 input buffer, one for the
            whole value and one for the integral value.
        min_allowed: Set the minimum value of the prompt. When the input value goes below this value, it
            will automatically reset to this value.
        max_allowed: Set the maximum value of the prompt. When the inptu value goes above this value, it
            will automatically reset to this value.
        qmark: Question mark symbol. Custom symbol that will be displayed infront of the question before its answered.
        amark: Answer mark symbol. Custom symbol that will be displayed infront of the question after its answered.
        decimal_symbol: Decimal point symbol. Custom symbol to display as the decimal point.
        replace_mode: Start each input buffer in replace mode if default value is 0.
            When typing, it will replace the 0 with the new value. The replace mode will be disabled once the value
            is changed.
        instruction: Short instruction to display next to the question.
        long_instruction: Long instructions to display at the bottom of the prompt.
        validate: Add validation to user input.
            Refer to :ref:`pages/validator:Validator` documentation for more details.
        invalid_message: Error message to display when user input is invalid.
            Refer to :ref:`pages/validator:Validator` documentation for more details.
        invalid_message: Error message to display when user input is invalid.
            Refer to :ref:`pages/validator:Validator` documentation for more details.
        transformer: A function which performs additional transformation on the value that gets printed to the terminal.
            Different than `filter` parameter, this is only visual effect and won’t affect the actual value returned by :meth:`~InquirerPy.base.simple.BaseSimplePrompt.execute`.
            Refer to :ref:`pages/dynamic:transformer` documentation for more details.
        filter: A function which performs additional transformation on the result.
            This affects the actual value returned by :meth:`~InquirerPy.base.simple.BaseSimplePrompt.execute`.
            Refer to :ref:`pages/dynamic:filter` documentation for more details.
        keybindings: Customise the builtin keybindings.
            Refer to :ref:`pages/kb:Keybindings` for more details.
        wrap_lines: Soft wrap question lines when question exceeds the terminal width.
        raise_keyboard_interrupt: Raise the :class:`KeyboardInterrupt` exception when `ctrl-c` is pressed. If false, the result
            will be `None` and the question is skiped.
        mandatory: Indicate if the prompt is mandatory. If True, then the question cannot be skipped.
        mandatory_message: Error message to show when user attempts to skip mandatory prompt.
        session_result: Used internally for :ref:`index:Classic Syntax (PyInquirer)`.

    Examples:
        >>> from InquirerPy import inquirer
        >>> result = inquirer.number(message="Enter number:").execute()
        >>> print(result)
        0
    """

    def __init__(
        self,
        message: InquirerPyMessage,
        style: Optional[InquirerPyStyle] = None,
        vi_mode: bool = False,
        default: InquirerPyDefault = 0,
        float_allowed: bool = False,
        max_allowed: Optional[Union[int, float]] = None,
        min_allowed: Optional[Union[int, float]] = None,
        decimal_symbol: str = ". ",
        replace_mode: bool = False,
        qmark: str = INQUIRERPY_QMARK_SEQUENCE,
        amark: str = "?",
        instruction: str = "",
        long_instruction: str = "",
        validate: Optional[InquirerPyValidate] = None,
        invalid_message: str = "Invalid input",
        transformer: Optional[Callable[[str], Any]] = None,
        filter: Optional[Callable[[str], Any]] = None,
        keybindings: Optional[InquirerPyKeybindings] = None,
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
            transformer=transformer,
            filter=filter,
            invalid_message=invalid_message,
            validate=validate,
            instruction=instruction,
            long_instruction=long_instruction,
            wrap_lines=wrap_lines,
            raise_keyboard_interrupt=raise_keyboard_interrupt,
            mandatory=mandatory,
            mandatory_message=mandatory_message,
            session_result=session_result,
        )

        self._float = float_allowed
        self._is_float = Condition(lambda: self._float)
        self._max = max_allowed
        self._min = min_allowed
        self._value_error_message = "Remove any non-integer value"
        self._decimal_symbol = decimal_symbol
        self._whole_replace = False
        self._integral_replace = False
        self._replace_mode = replace_mode

        self._leading_zero_pattern = re.compile(r"^(0*)[0-9]+.*")
        self._sn_pattern = re.compile(r"^.*E-.*")
        self._no_default = False

        if default is None:
            default = 0
            self._no_default = True

        if isinstance(default, Callable):
            default = cast(Callable, default)(session_result)
        if self._float:
            default = Decimal(str(float(cast(int, default))))
        if self._float:
            if not isinstance(default, float) and not isinstance(default, Decimal):
                raise InvalidArgument(
                    f"{type(self).__name__} argument 'default' should return type of float or Decimal"
                )
        elif not isinstance(default, int):
            raise InvalidArgument(
                f"{type(self).__name__} argument 'default' should return type of int"
            )
        self._default = default

        if keybindings is None:
            keybindings = {}
        self.kb_maps = {
            "down": [
                {"key": "down"},
                {"key": "c-n", "filter": ~self._is_vim_edit},
                {"key": "j", "filter": self._is_vim_edit},
            ],
            "up": [
                {"key": "up"},
                {"key": "c-p", "filter": ~self._is_vim_edit},
                {"key": "k", "filter": self._is_vim_edit},
            ],
            "left": [
                {"key": "left"},
                {"key": "c-b", "filter": ~self._is_vim_edit},
                {"key": "h", "filter": self._is_vim_edit},
            ],
            "right": [
                {"key": "right"},
                {"key": "c-f", "filter": ~self._is_vim_edit},
                {"key": "l", "filter": self._is_vim_edit},
            ],
            "dot": [{"key": "."}],
            "focus": [{"key": Keys.Tab}, {"key": "s-tab"}],
            "input": [{"key": str(i)} for i in range(10)],
            "negative_toggle": [{"key": "-"}],
            **keybindings,
        }
        self.kb_func_lookup = {
            "down": [{"func": self._handle_down}],
            "up": [{"func": self._handle_up}],
            "left": [{"func": self._handle_left}],
            "right": [{"func": self._handle_right}],
            "focus": [{"func": self._handle_focus}],
            "input": [{"func": self._handle_input}],
            "negative_toggle": [{"func": self._handle_negative_toggle}],
            "dot": [{"func": self._handle_dot}],
        }

        @self.register_kb(Keys.Any)
        def _(_):
            pass

        self._whole_width = 1
        self._whole_buffer = Buffer(
            on_text_changed=self._on_whole_text_change,
            on_cursor_position_changed=self._on_cursor_position_change,
        )

        self._integral_width = 1
        self._integral_buffer = Buffer(
            on_text_changed=self._on_integral_text_change,
            on_cursor_position_changed=self._on_cursor_position_change,
        )

        self._whole_window = Window(
            height=LayoutDimension.exact(1) if not self._wrap_lines else None,
            content=BufferControl(
                buffer=self._whole_buffer,
                lexer=SimpleLexer("class:input"),
            ),
            width=lambda: Dimension(
                min=self._whole_width,
                max=self._whole_width,
                preferred=self._whole_width,
            ),
            dont_extend_width=True,
        )

        self._integral_window = Window(
            height=LayoutDimension.exact(1) if not self._wrap_lines else None,
            content=BufferControl(
                buffer=self._integral_buffer,
                lexer=SimpleLexer("class:input"),
            ),
            width=lambda: Dimension(
                min=self._integral_width,
                max=self._integral_width,
                preferred=self._integral_width,
            ),
        )

        self._layout = Layout(
            HSplit(
                [
                    VSplit(
                        [
                            Window(
                                height=LayoutDimension.exact(1)
                                if not self._wrap_lines
                                else None,
                                content=FormattedTextControl(self._get_prompt_message),
                                wrap_lines=self._wrap_lines,
                                dont_extend_height=True,
                                dont_extend_width=True,
                            ),
                            ConditionalContainer(self._whole_window, filter=~IsDone()),
                            ConditionalContainer(
                                Window(
                                    height=LayoutDimension.exact(1)
                                    if not self._wrap_lines
                                    else None,
                                    content=FormattedTextControl(
                                        [("", self._decimal_symbol)]
                                    ),
                                    wrap_lines=self._wrap_lines,
                                    dont_extend_height=True,
                                    dont_extend_width=True,
                                ),
                                filter=self._is_float & ~IsDone(),
                            ),
                            ConditionalContainer(
                                self._integral_window, filter=self._is_float & ~IsDone()
                            ),
                        ],
                        align=HorizontalAlign.LEFT,
                    ),
                    ConditionalContainer(
                        Window(content=DummyControl()),
                        filter=~IsDone() & self._is_displaying_long_instruction,
                    ),
                    ValidationWindow(
                        invalid_message=self._get_error_message,
                        filter=self._is_invalid & ~IsDone(),
                        wrap_lines=self._wrap_lines,
                    ),
                    InstructionWindow(
                        message=self._long_instruction,
                        filter=~IsDone() & self._is_displaying_long_instruction,
                        wrap_lines=self._wrap_lines,
                    ),
                ]
            ),
        )

        self.focus = self._whole_window

        self._application = Application(
            layout=self._layout,
            style=self._style,
            key_bindings=self._kb,
            after_render=self._after_render,
            editing_mode=self._editing_mode,
        )

    def _fix_sn(self, value: str) -> Tuple[str, str]:
        """Fix sciencetific notation format.

        Args:
            value: Value to fix.

        Returns:
            A tuple of whole buffer text and integral buffer text.
        """
        pass

    def _on_rendered(self, _) -> None:
        """Additional processing to adjust buffer content after render."""
        pass

    def _handle_number(self, increment: bool) -> None:
        """Handle number increment and decrement.

        Additional processing to handle leading zeros in integral buffer
        as well as SN notation.

        Args:
            increment: Indicate if the operation should increment or decrement.
        """
        pass

    def _handle_down(self, _) -> None:
        """Handle down key press."""
        pass

    def _handle_up(self, _) -> None:
        """Handle up key press."""
        pass

    def _handle_left(self, _) -> None:
        """Handle left key press.

        Move to the left by one cursor position and focus the whole window
        if applicable.
        """
        pass

    def _handle_right(self, _) -> None:
        """Handle right key press.

        Move to the right by one cursor position and focus the integral window
        if applicable.
        """
        pass

    def _handle_enter(self, event: "KeyPressEvent") -> None:
        """Handle enter event and answer/close the prompt."""
        pass

    def _handle_dot(self, _) -> None:
        """Focus the integral window if `float_allowed`."""
        pass

    def _handle_focus(self, _, window: Optional[Window] = None) -> None:
        """Focus either the integral window or whole window."""
        pass

    def _handle_input(self, event: "KeyPressEvent") -> None:
        """Handle user input of numbers.

        Buffer will start as replace mode if the value is zero, once
        cursor is moved or content is changed, disable replace mode.
        """
        pass

    def _handle_negative_toggle(self, _) -> None:
        """Toggle negativity of the prompt value.

        Force the `-` sign at the start.
        """
        pass

    def _on_whole_text_change(self, buffer: Buffer) -> None:
        """Handle event of text changes in buffer."""
        pass

    def _on_integral_text_change(self, buffer: Buffer) -> None:
        """Handle event of text changes in buffer."""
        pass

    def _on_text_change(self, buffer: Buffer) -> None:
        """Disable replace mode and fix cursor position on text changes."""
        pass

    def _on_cursor_position_change(self, buffer: Buffer) -> None:
        """Fix cursor position on cursor movement."""
        pass

    @property
    def buffer_replace(self) -> bool:
        """bool: Current buffer replace mode."""
        pass

    @buffer_replace.setter
    def buffer_replace(self, value) -> None:
        pass

    @property
    def focus_buffer(self) -> Buffer:
        """Buffer: Current editable buffer."""
        pass

    @property
    def focus(self) -> Window:
        """Window: Current focused window."""
        pass

    @focus.setter
    def focus(self, value: Window) -> None:
        pass

    @property
    def value(self) -> Union[int, float, Decimal]:
        """Union[int, float]: The actual value of the prompt, combining and transforming all input buffer values."""
        pass

    @value.setter
    def value(self, value: Union[int, float, Decimal]) -> None:
        pass
