import tkinter as tk
from tkinter import ttk
from typing import Literal, TypedDict


VariableType = Literal[
    'string', 's',
    'boolean', 'b', 'bool',
    'int', 'integer', 'i',
    'float', 'f',
    'list', 'l',
]

Position = Literal[
    'top right', 'tr', 'topright', 'top-right',
    'top left', 'tl', 'topleft', 'top-left',
    'bottom right', 'br', 'bottomright', 'bottom-right',
    'bottom left', 'bl', 'bottomleft', 'bottom-left',
    'centre', 'center', 'c',
]

WidgetType = Literal[
    'combobox', 'combo', 'dropdown',
    'spinbox', 'spin',
    'scale', 'slider',
    'checkbox', 'check',
    'textbox', 'entry', 'text',
]


class ButtonConfig(TypedDict, total=False):
    frame: int
    text: str


class OptionsSelectionFrame:

    def __init__(
        self,
        title: str,
        columns: int,
        height: int,
        width: int,
        position: Position,
        button: ButtonConfig | None = None,
    ) -> None:
        """Initialize a tkinter window with a grid of column frames.

        Args:
            title: Window title.
            columns: Number of columns in the layout.
            height: Window height in pixels.
            width: Window width in pixels.
            position: Window placement on screen.
            button: Optional config for the submit button. Keys are ``frame``
                (column index, default 0) and ``text`` (label, default ``'Run'``).
        """
        self.root = tk.Tk()
        self.root.title(title)

        self.set_geometry(height, width, position)

        self.frames: list[tk.Frame] = []
        for col in range(columns):
            self.root.columnconfigure(col, weight=1)
            frame = tk.Frame(self.root, padx=2, pady=10)
            frame.grid(row=0, column=col, padx=10, pady=10, sticky='ew')
            self.frames.append(frame)

        if button is not None:
            self.submit_button = ttk.Button(
                self.frames[button.get('frame', 0)],
                text=button.get('text', 'Run'),
                command=self._on_submit,
            )
        else:
            self.submit_button = ttk.Button(self.frames[0], text='Run', command=self._on_submit)

        self.widgets: dict[str, OptionsSelectionWidget] = {}
        self.values: dict[str, object] = {}

    def run(self) -> None:
        """Pack the submit button and start the tkinter event loop."""
        # add submit button last so it appears at the bottom
        self.submit_button.pack(pady=30)
        self.root.mainloop()

    def set_geometry(self, height: int, width: int, position: Position) -> None:
        """Set the window size and screen position.

        Args:
            height: Window height in pixels.
            width: Window width in pixels.
            position: Where to place the window. Accepted values:
                ``'top right'``, ``'tr'``, ``'topright'``, ``'top-right'``;
                ``'top left'``, ``'tl'``, ``'topleft'``, ``'top-left'``;
                ``'bottom right'``, ``'br'``, ``'bottomright'``, ``'bottom-right'``;
                ``'bottom left'``, ``'bl'``, ``'bottomleft'``, ``'bottom-left'``;
                ``'centre'``, ``'center'``, ``'c'``.

        Raises:
            ValueError: If ``position`` is not one of the accepted values.
        """
        padding = 20

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        if 'left' in position or position in ('tl', 'bl'):
            x = padding
        elif 'right' in position or position in ('tr', 'br'):
            x = screen_width - width - padding
        elif position in ('centre', 'center', 'c'):
            x = screen_width / 2 - width / 2
        else:
            raise ValueError(f"OptionsSelection position argument not recognized: {position!r}")

        if 'top' in position or position in ('tl', 'tr'):
            y = padding
        elif 'bottom' in position or position in ('bl', 'br'):
            y = screen_height - height - padding - 75  # subtract 75 for the Windows taskbar
        elif position in ('centre', 'center', 'c'):
            y = screen_height / 2 - height / 2
        else:
            raise ValueError(f"OptionsSelection position argument not recognized: {position!r}")

        self.root.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    def add_widget(
        self,
        variable_type: VariableType,
        text: str,
        options: list | None,
        column: int,
        default_value: object = None,
        widget_type: WidgetType | None = None,
        scale_resolution: float | None = None,
    ) -> None:
        """Create and register a widget in the specified column.

        Args:
            variable_type: Type of value the widget holds.
            text: Display label for the widget; must be unique across all widgets.
            options: Allowed values (required for dropdowns and sliders).
            column: Zero-based column index to place the widget in.
            default_value: Initial value for the widget.
            widget_type: Override the automatically inferred widget type.
            scale_resolution: Step size for slider widgets.

        Raises:
            ValueError: If ``text`` is already registered as a widget label.
        """
        if text in self.widgets:
            raise ValueError(f'Widget text "{text}" already exists')
        self.widgets[text] = OptionsSelectionWidget(
            variable_type=variable_type,
            text=text,
            options=options,
            frame=self.frames[column],
            default_value=default_value,
            widget_type=widget_type,
            scale_resolution=scale_resolution,
        )

    def _on_submit(self) -> None:
        """Collect current widget values and close the window."""
        for text, widget in self.widgets.items():

            if widget.widget_type == 'listbox':
                self.values[text] = [widget.widget.get(i) for i in widget.widget.curselection()]
            else:
                self.values[text] = widget.widget.get()

        self.root.quit()
        self.root.destroy()


class OptionsSelectionWidget:

    @staticmethod
    def create_variable(variable_type: VariableType, default_value: object) -> tk.Variable:
        """Create a tkinter variable matching the given type.

        Args:
            variable_type: Type of value the variable will hold.
            default_value: Initial value for the tk variable.

        Returns:
            A ``tk.StringVar``, ``tk.BooleanVar``, ``tk.IntVar``, or
            ``tk.DoubleVar`` matching ``variable_type``.

        Raises:
            NotImplementedError: If ``variable_type`` is not supported.
        """
        if variable_type in ('string', 's'):
            return tk.StringVar(value=default_value)
        elif variable_type in ('boolean', 'b', 'bool'):
            return tk.BooleanVar(value=default_value)
        elif variable_type in ('int', 'integer', 'i'):
            return tk.IntVar(value=default_value)
        elif variable_type in ('float', 'f'):
            return tk.DoubleVar(value=default_value)
        raise NotImplementedError(f'Variable type {variable_type!r} not implemented in tkinter')

    @staticmethod
    def imply_widget_type(variable_type: VariableType, options: list | None = None) -> WidgetType:
        """Infer the default widget type for a given variable type.

        Strings with options become a combobox; without options, a textbox.
        Booleans become a checkbox. Integers and floats become a scale (slider).

        Args:
            variable_type: Type of value the widget will hold.
            options: Allowed values; influences the inferred type for strings.

        Returns:
            The inferred widget type.

        Raises:
            NotImplementedError: If ``variable_type`` has no default widget mapping.
        """
        if variable_type in ('string', 's'):
            return 'combobox' if options else 'textbox'
        elif variable_type in ('boolean', 'b', 'bool'):
            return 'checkbox'
        elif variable_type in ('int', 'integer', 'i', 'float', 'f'):
            return 'scale'
        raise NotImplementedError(f'Widget type for variable type {variable_type!r} not implemented')

    @staticmethod
    def create_widget(
        widget_type: WidgetType,
        options: list | None,
        final_variable: tk.Variable,
        frame: tk.Frame,
        scale_resolution: float | None = None,
    ) -> tk.Widget | None:
        """Create, pack, and return a tkinter widget.

        Returns the widget for types that support ``.get()`` directly
        (combobox, spinbox, scale, entry). Returns ``None`` for checkbox,
        which requires reading its bound variable instead.

        Raises:
            NotImplementedError: If ``widget_type`` is not supported.
        """
        if widget_type in ('combobox', 'combo', 'dropdown'):
            dropdown = ttk.Combobox(frame, textvariable=final_variable, height=len(options) + 1)
            dropdown['values'] = options
            dropdown.pack(fill='x', padx=10)
            return dropdown
        elif widget_type in ('spinbox', 'spin'):
            spinbox = tk.Spinbox(frame, from_=min(options), to=max(options), textvariable=final_variable)
            spinbox.pack(fill='x', padx=10)
            return spinbox
        elif widget_type in ('scale', 'slider'):
            scale = tk.Scale(
                frame,
                from_=min(options),
                to=max(options),
                variable=final_variable,
                orient=tk.HORIZONTAL,
                resolution=scale_resolution,
            )
            scale.pack(fill='x', padx=10)
            return scale
        elif widget_type in ('checkbox', 'check'):
            checkbox = tk.Checkbutton(frame, variable=final_variable)
            checkbox.pack()
            return None  # Checkbutton has no .get(); read the variable instead
        elif widget_type in ('textbox', 'entry', 'text'):
            entry = tk.Entry(frame, textvariable=final_variable)
            entry.pack(fill='x', padx=10)
            return entry
        else:
            raise NotImplementedError(f'Widget type {widget_type!r} not implemented')

    def __init__(
        self,
        variable_type: VariableType,
        text: str,
        options: list | None,
        frame: tk.Frame,
        default_value: object = None,
        widget_type: WidgetType | None = None,
        scale_resolution: float | None = None,
    ) -> None:
        """Build and pack a labelled widget into the given frame.

        Args:
            variable_type: Type of value the widget will hold.
            text: Display label rendered above the widget.
            options: Allowed values (required for dropdowns and sliders).
            frame: Parent tkinter frame.
            default_value: Initial value for the widget.
            widget_type: Override the automatically inferred widget type.
            scale_resolution: Step size for slider widgets.
        """
        self.text = text

        label = ttk.Label(frame, text=text)
        label.pack(fill='x', padx=10, pady=5)

        if variable_type in ('list', 'l'):
            listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, exportselection=False, height=len(options) + 1)
            listbox.pack(fill='x', padx=10, pady=5)

            for item in options:
                listbox.insert(tk.END, item)

            if default_value is not None:
                for item in default_value:
                    listbox.select_set(options.index(item))

            self.widget_type = 'listbox'
            self.widget = listbox
            return

        widget_variable = self.create_variable(variable_type, default_value)

        if widget_type is None:
            widget_type = self.imply_widget_type(variable_type, options)
        self.widget_type: str = widget_type.lower()

        if self.widget_type in ('scale', 'slider') and scale_resolution is None:
            scale_resolution = 0.01 if variable_type in ('float', 'f') else 1

        actual_widget = self.create_widget(self.widget_type, options, widget_variable, frame, scale_resolution)

        separator = ttk.Separator(frame, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=5)

        # Use the actual widget's .get() where available; fall back to the
        # variable for checkbox (Checkbutton has no .get()).
        self.widget = actual_widget if actual_widget is not None else widget_variable


if __name__ == '__main__':
    frame = OptionsSelectionFrame('example', columns=3, height=480, width=500, position='topright')

    frame.add_widget('list', 'websites', ['google', 'facebook', 'youtube', 'twitter'], default_value=['facebook', 'twitter'], column=0)
    frame.add_widget('b', 'has_account', default_value=True, column=0, options=None)
    frame.add_widget('b', 'like_posts', default_value=False, column=0, options=None)
    frame.add_widget('i', 'Number of posts to like', [1, 7], default_value=3, column=1)
    frame.add_widget('string', 'Comment', ['I love this', 'Amazing', 'Super awesome!'], default_value='Amazing', column=2)
    frame.add_widget('s', 'Custom message', options=None, default_value='Type here...', column=2)

    frame.run()

    print(frame.values)
    print(f'We will comment {frame.values["Comment"]} on every post.')
