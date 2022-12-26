#!/usr/bin/env python3

import tkinter as tk
from tkinter import Tk, ttk
import logging
import lightlib
import smokesignal


class LightWidget:
    def __init__(self, master, light: lightlib.Light):
        self.frame = ttk.Frame(master, padding=10)
        self.frame.grid()
        self._label = ttk.Label(self.frame, text=light.signal_name)
        self._label.grid(column=0, row=0)

        self._indicator = ttk.Label(self.frame)
        self._indicator.grid(column=0, row=1)

        self._role_indicator = ttk.Label(self.frame)
        self._role_indicator.grid(column=0, row=2)

        self._toggle_button = ttk.Button(self.frame, text="disable", command=self._toggle)
        self._toggle_button.grid(column=0, row=3)

        self._light = light
        smokesignal.on(self._light.signal_name, self._on_light_state_change)
        self._light.start()

    def _toggle(self):
        self._toggle_button["text"] = "⏳"
        self._toggle_button["state"] = "disabled"
        if self._light.is_enabled:
            smokesignal.once(f"{self._light.signal_name}-toggled", self._on_disabled)
            self._light.disable()
        else:
            self._toggle_button["state"] = "disabled"
            smokesignal.once(f"{self._light.signal_name}-toggled", self._on_enabled)
            self._light.enable()

    def _on_disabled(self):
        self._toggle_button["state"] = "enabled"
        self._toggle_button["text"] = "enable"

    def _on_enabled(self):
        self._toggle_button["state"] = "enabled"
        self._toggle_button["text"] = "disable"

    def _on_light_state_change(self, is_on):
        self._indicator["text"] = "🔴" if is_on else "⚪️"
        self._role_indicator["text"] = "👨‍✈️ MASTER" if self._light.is_master else ""

    def shutdown(self):
        if self._light.is_alive():
            self._light.stop()


class TextBoxLoggingHandler(logging.Handler):
    def __init__(self, widget: tk.Text) -> None:
        super().__init__()
        self._widget = widget

    def emit(self, record: logging.LogRecord) -> None:
        self._widget.insert(tk.END, self.format(record) + "\n")
        self._widget.see(tk.END)


def main():
    root = Tk()
    root_logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s %(levelname)8s %(name)s: %(message)s")
    root_logger.setLevel(logging.INFO)

    frm_bottom = ttk.Frame(root, padding=10)
    frm_bottom.grid(column=0, row=1)
    log = tk.Text(root)
    log.grid()
    gui_handler = TextBoxLoggingHandler(log)
    gui_handler.setFormatter(formatter)
    root_logger.addHandler(gui_handler)

    frm = ttk.Frame(root, padding=10)
    frm.grid(column=0, row=0)
    light_widgets = []
    for row in range(3):
        for column in range(3):
            light_frame = ttk.Frame(frm, padding=10)
            light = lightlib.Light()
            light_widgets.append(LightWidget(light_frame, light))
            light_frame.grid(column=column, row=row)

    def shutdown():
        nonlocal root
        root.destroy()

        nonlocal light_widgets
        for widget in light_widgets:
            widget.shutdown()

    debug_val = tk.IntVar(frm, 0)

    def toggle_log_level():
        nonlocal root_logger
        nonlocal debug_val
        root_logger.setLevel(logging.DEBUG if debug_val.get() == 1 else logging.INFO)

    ttk.Button(frm, text="Quit", command=shutdown).grid(column=5, row=0)
    debug_chk = ttk.Checkbutton(frm, text="debug", command=toggle_log_level,
                                variable=debug_val)
    debug_chk.grid(column=5, row=1)
    root.mainloop()


if __name__ == "__main__":
    main()
