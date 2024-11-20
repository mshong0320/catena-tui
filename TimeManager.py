"""
TimeManager Module

This module provides the `TimeManager` class for managing system time configurations within a terminal-based
user interface using `urwid`. It allows users to view the current system time, update it, and optionally reboot
the system for changes to take effect. The class can also operate in an initial setup mode for guided configuration.

Classes:
    - TimeManager: A configurable UI component for managing and setting system time.

Dependencies:
    - urwid
    - subprocess
    - logging
    - typing
    - datetime
"""

import urwid
import subprocess
import logging
import typing
from datetime import datetime

class TimeManager(urwid.WidgetWrap):
    signals: typing.ClassVar[list[str]] = ["close"]

    def __init__(self, initial_setup: bool = False) -> None:
        """
        Initialize the TimeManager class.

        Args:
            initial_setup (bool): Determines if the TimeManager operates in initial setup mode. Default is False.
        """
        logging.debug('Initializing TimeManager')
        self.current_time = self.get_current_time()
        self.current_time_show = urwid.Text(f"Current Time: {self.current_time}")
        self.current_time_padded = urwid.Padding(self.current_time_show, 'center', width=('relative', 50))
        self.reboot_button = urwid.Button("Reboot", self.reboot_system)
        self.back_button = urwid.Button("Back", self.exit_to_menu)
        self.backWrapped = urwid.Padding(urwid.AttrMap(self.back_button, 'selectable'), 'left', 20)
        self.rebootWrapped = urwid.Padding(urwid.AttrMap(self.reboot_button, 'selectable'), 'left', 20)
        self.time_input = urwid.Edit("Please enter new time (format: YYYY-MM-DD HH:MM:SS): ", edit_text="", multiline=False)
        self.time_input_wrapped = urwid.Padding(self.time_input, 'center', width=('relative', 50))
        self.submit_button = urwid.Button("Submit", on_press=self.submit)
        self.submit_button_wrapped = urwid.Padding(urwid.AttrMap(self.submit_button, 'selectable'), 'left', 20)
        self.initial_setup = initial_setup
        self.create_layout()
        logging.debug('TimeManager initialized')

    def submit(self, button):
        """
        Submit the new system time entered by the user.

        Args:
            button: The button triggering this action.
        """
        try:
            new_time = self.time_input.edit_text
            try:
                datetime.strptime(new_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("Invalid time format. Please enter the time as 'YYYY-MM-DD HH:MM:SS'.")
            # Disable NTP
            subprocess.check_output(['sudo', 'timedatectl', 'set-ntp', 'false'], text=True)
            # Set the system time
            subprocess.check_output(['sudo', 'timedatectl', 'set-time', new_time])
            self.current_time = new_time
            self.current_time_show.set_text(f"Current Time: {self.current_time}")
        except ValueError as ve:
            logging.error(f"Validation error: {ve}")
            error_text = urwid.Text(f"Error: {ve}")
            self.pile.contents.append((error_text, ('pack', None)))
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set time: {e}")
            error_text = urwid.Text(f"Error setting system time: {e}")
            self.pile.contents.append((error_text, ('pack', None)))
        finally:
            self.reset_layout()

    def get_current_time(self):
        """
        Get the current system time.

        Returns:
            str: The current system time as a string.
        """
        try:
            output = subprocess.check_output(['timedatectl', 'status'], text=True)
            for line in output.splitlines():
                if "Local time" in line:
                    current_time = line.strip().split(": ", 1)[1]
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            current_time = "Failed to Determine Time"
        return current_time

    def create_layout(self):
        """
        Create the initial layout of the TimeManager UI.
        """
        if self.initial_setup == False:
            self.pile = urwid.Pile([
                self.current_time_padded,
                urwid.Divider(),
                self.time_input_wrapped,
                urwid.Divider(),
                self.submit_button_wrapped,
                urwid.Divider(),
                self.backWrapped,
                urwid.Divider(),
                self.rebootWrapped
            ])
        else:
            self.pile = urwid.Pile([
                self.current_time_padded,
                urwid.Divider(),
                self.time_input_wrapped,
                urwid.Divider(),
                self.submit_button_wrapped,
            ])
        self.box = urwid.LineBox(urwid.Filler(self.pile, valign='top'), title="Configure Time")
        super().__init__(self.box)

    def reset_layout(self, *args):
        """
        Reset the layout after the time is set or an error occurs.
        """
        self.pile.contents.clear()
        if self.initial_setup == False:
            success_message = urwid.Text(f"Time is successfully set to {self.current_time}. Please reboot.")
        else:
            success_message = urwid.Text(f"Time is successfully set to {self.current_time}. Click the Next button.")
        success_message_padded = urwid.Padding(success_message, 'center', width=('relative', 50))
        current_time_padded = urwid.Padding(self.current_time_show, 'center', width=('relative', 50))
        self.time_input = urwid.Edit("Please enter new time (format: YYYY-MM-DD HH:MM:SS): ", edit_text="", multiline=False)
        self.time_input_wrapped = urwid.Padding(self.time_input, 'center', width=('relative', 50))

        if self.initial_setup == False:
            new_pile_content = [
                urwid.Text(""),
                current_time_padded,
                urwid.Text(""),
                success_message_padded,
                urwid.Text(""),
                self.time_input_wrapped,
                urwid.Text(""),
                self.submit_button_wrapped,
                urwid.Text(""),
                self.backWrapped,
                urwid.Text(""),
                self.rebootWrapped
            ]
            self.pile.contents.extend([(widget, ('pack', None)) for widget in new_pile_content])
        else:
            new_pile_content = [
                urwid.Text(""),
                current_time_padded,
                urwid.Text(""),
                success_message_padded,
                urwid.Text(""),
                self.time_input_wrapped,
                urwid.Text(""),
                self.submit_button_wrapped,
            ]
            self.pile.contents.extend([(widget, ('pack', None)) for widget in new_pile_content])

    def reboot_system(self, button):
        """
        Reboot the system.

        Args:
            button: The button triggering this action.
        """
        try:
            subprocess.run("sudo reboot", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            response_text = urwid.Text(f"Failed to reboot system: {e}")
            self.pile.contents.insert(1, (urwid.AttrMap(response_text, None), ('pack', None)))

    def exit_to_menu(self, button):
        """
        Exit to the main menu.

        Args:
            button: The button triggering this action.
        """
        self._emit('close')
        self.reset_layout()
