"""
This module defines the HostnameManager class, which provides a terminal-based UI for configuring the system's hostname.
It uses the Urwid library to display an interactive menu, allowing the user to 
input a new hostname, submit it, and reboot the system.

Features:
- Displays the current system hostname.
- Allows the user to input a new hostname.
- Provides buttons for submitting the new hostname and rebooting the system.
- Includes a "Back" button to exit the hostname configuration screen and return to the main menu.
- In initial setup mode, only basic options are presented, and a reboot button is shown after changing the hostname.

The HostnameManager class also emits a "close" signal when the "Back" button is clicked,
allowing it to communicate with the rest of the application.

Dependencies:
- urwid: A Python library for creating console user interfaces.
- subprocess: Used to run system commands for setting the hostname and rebooting the system.
- logging: For logging various events and errors during execution.
- platform: Used to retrieve the current system's hostname.

Usage:
    The HostnameManager is instantiated and can be added to an Urwid main loop as a widget.
    The user can interact with the UI to change the system's hostname.
"""

import urwid
import subprocess
import logging
import typing
import platform
logger = logging.getLogger(__name__)


class HostnameManager(urwid.WidgetWrap):
    """
    A class to manage and configure the system's hostname using a terminal-based UI with Urwid.
    This class allows the user to change the system hostname and provides options to reboot the system.
    It supports an initial setup mode where the user is guided through the process of setting a hostname.

    Signals:
        close: Emitted when the user exits the menu.
    """
    signals: typing.ClassVar[list[str]] = ["close"]

    def __init__(self, initial_setup: bool = False) -> None:
        logging.debug('Initializing HostnameManager')
        self.initial_setup = initial_setup
        self.create_layout()
        logging.debug('HostnameManager initialized')

    def create_layout(self):
        """
        Creates the layout of the terminal UI for configuring the hostname.
        This layout includes fields for inputting a new hostname, displaying the current hostname,
        and buttons for submitting the hostname, rebooting, and returning to the menu.
        """
        self.current_hostname = platform.node()
        self.hostname_input = urwid.Edit("Enter new hostname:   ")
        self.current_hostname_display = urwid.Text(f"Current Hostname: {self.current_hostname}")
        self.hostname_input_padded = urwid.Padding(self.hostname_input, 'center', width=('relative', 50))
        self.current_hostname_padded = urwid.Padding(self.current_hostname_display, 'center', width=('relative', 50))
        submit_button = urwid.Button("Submit", self.submit_hostname)
        self.submitWrapped = urwid.Padding(urwid.AttrMap(submit_button, 'selectable'), 'left', 12)
        self.reboot_button = urwid.Button("Reboot", self.reboot_system)
        back_button = urwid.Button("Back", self.exit_to_menu)
        self.backWrapped = urwid.Padding(urwid.AttrMap(back_button, 'selectable'), 'left', 12)
        self.rebootWrapped = urwid.Padding(urwid.AttrMap(self.reboot_button, 'selectable'), 'left', 12)
        self.reboot_button_displayed = False
        if self.initial_setup == False:
            self.pile = urwid.Pile([
                self.hostname_input_padded,
                urwid.Divider(),
                self.current_hostname_padded,
                urwid.Divider(),
                self.submitWrapped,
                self.backWrapped,
                self.rebootWrapped
            ])
            self.pile.contents[-1] = (urwid.Text(''), ('pack', None))
        else:
            self.pile = urwid.Pile([
                self.hostname_input_padded,
                urwid.Divider(),
                self.current_hostname_padded,
                urwid.Divider(),
                self.submitWrapped
            ])
        self.box = urwid.LineBox(urwid.Filler(self.pile), title="Configure Hostname")
        super().__init__(self.box)

    def submit_hostname(self, button: urwid.Button) -> None:
        """
        Handles the logic for submitting a new hostname. The hostname input is validated and set if valid.
        If successful, it updates the display with the new hostname and optionally shows the Reboot button.
        If unsuccessful, it displays an error message.
        Args:
            button (urwid.Button): The button that triggered this action.
        """
        logging.debug('Submit button clicked')
        new_hostname = self.hostname_input.get_edit_text().strip()
        logging.debug(f'New hostname input: {new_hostname}')
        if self.initial_setup == False:
            self.pile.contents = [
                (urwid.Padding(self.hostname_input, 'center', width=('relative', 50)), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Padding(self.current_hostname_display, 'center', width=('relative', 50)), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (self.submitWrapped, ('pack', None)),
                (self.backWrapped, ('pack', None)),
                (self.rebootWrapped, ('pack', None))
            ]
        else:
            self.pile.contents = [
                (urwid.Padding(self.hostname_input, 'center', width=('relative', 50)), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Padding(self.current_hostname_display, 'center', width=('relative', 50)), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (self.submitWrapped, ('pack', None)),
            ]
        if new_hostname:
            try:
                subprocess.run(f"sudo hostnamectl set-hostname {new_hostname}", shell=True, check=True)
                logger.info(f"Hostname changed to: {new_hostname}")
                self.current_hostname = new_hostname
                self.current_hostname_display.set_text(f"Current Hostname: {self.current_hostname}")
                if self.initial_setup==False:
                    response_text = urwid.Text(f"Hostname changed to: {self.current_hostname}. Please reboot.")
                else:
                    response_text = urwid.Text(f"Hostname changed to: {self.current_hostname}. Please click Next")
                response_text_padded = urwid.Padding(response_text, 'center', width=('relative', 50))
                self.pile.contents.insert(3, (urwid.AttrMap(response_text_padded, None), ('pack', None)))
                if not self.reboot_button_displayed and self.initial_setup:
                    self.pile.contents[-1] = (self.rebootWrapped, ('pack', None))
                    self.reboot_button_displayed = True
                self.hostname_input.set_edit_text("")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to set hostname: {e}")
                response_text = urwid.Text(f"Failed to change hostname: {e}")
                response_text_padded = urwid.Padding(response_text, 'center', width=('relative', 50))
                self.pile.contents.insert(3, (urwid.AttrMap(response_text_padded, None), ('pack', None)))
        else:
            response_text = urwid.Text("Please provide a valid hostname.")
            response_text_padded = urwid.Padding(response_text, 'center', width=('relative', 50))
            self.pile.contents.insert(3, (urwid.AttrMap(response_text_padded, None), ('pack', None)))

    def reboot_system(self, button: urwid.Button) -> None:
        logging.debug('Reboot button clicked')
        try:
            subprocess.run("sudo reboot", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reboot: {e}")
            response_text = urwid.Text(f"Failed to reboot system: {e}")
            self.pile.contents.insert(1, (urwid.AttrMap(response_text, None), ('pack', None)))

    def screen_reset(self):
        """
        Resets the screen layout to its initial state, clearing any messages
        and restoring the hostname configuration form.
        """
        self.pile = urwid.Pile([
            self.hostname_input_padded,
            urwid.Divider(),
            self.current_hostname_padded,
            urwid.Divider(),
            self.submitWrapped,
            self.backWrapped,
        ])
        self.box = urwid.LineBox(urwid.Filler(self.pile), title="Configure Hostname")
        super().__init__(self.box)

    def exit_to_menu(self, button: urwid.Button) -> None:
        logging.debug('Back button clicked, restarting layout')
        self.screen_reset()
        self._emit('close')
