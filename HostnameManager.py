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

    def __init__(self, setup_wizard: bool = False):
        logging.debug('Initializing HostnameManager')
        self.setup_wizard = setup_wizard
        self.current_hostname = platform.node()
        self.create_widgets()
        self.create_layout()
        logging.debug('HostnameManager initialized')

    def create_widgets(self):
        """
        Initialize the widgets for the hostname manager.
        """
        self.hostname_input = urwid.Edit("Enter new hostname:   ", edit_text="", multiline=False)
        self.hostname_input.set_edit_text(self.current_hostname)
        self.hostname_input_padded = urwid.Pile([
            urwid.LineBox(
                urwid.Padding(
                    urwid.AttrMap(self.hostname_input, "editbox", "editbox_focus"),
                    align='center', width=('relative', 50)
                )
            )
        ])
        submit_button = urwid.Button("Submit", self.submit_hostname)
        self.submitWrapped = urwid.Padding(urwid.AttrMap(submit_button, 'selectable'), 'left', 12)

        back_button = urwid.Button("Back", self.exit_to_menu)
        self.backWrapped = urwid.Padding(urwid.AttrMap(back_button, 'selectable'), 'left', 12)

        reboot_button = urwid.Button("Reboot", self.reboot_system)
        self.rebootWrapped = urwid.Padding(urwid.AttrMap(reboot_button, 'selectable'), 'left', 12)

        self.response_widget = urwid.Text("")
        self.response_widget_padded = urwid.Padding(self.response_widget, 'center', width=('relative', 50))

    def create_layout(self):
        """
        Creates the layout of the UI based on the initial_setup condition.
        """
        # Common elements
        self.pile = urwid.Pile([
            self.hostname_input_padded,
            self.response_widget_padded,
            self.submitWrapped
        ])

        # Additional elements only if initial_setup is None
        if not self.setup_wizard:
            self.pile.contents.append((self.backWrapped, ('pack', None)))
            self.pile.contents.append((self.rebootWrapped, ('pack', None)))

        self.box = urwid.LineBox(urwid.Filler(self.pile), title="Configure Hostname")
        super().__init__(self.box)

    def submit_hostname(self, button: urwid.Button) -> None:
        """
        Handles the logic for submitting a new hostname.
        Ensures the new hostname is different from the current one.
        Clears the input field after submission and updates the response display.
        """
        logging.debug('Submit button clicked')
        new_hostname = self.hostname_input.get_edit_text().strip()

        # Clear any existing response message
        self.clear_response()

        if not new_hostname:
            self.display_response("Please provide a valid hostname.")
            self.hostname_input.set_edit_text("")
            return
        if new_hostname == self.current_hostname:
            self.display_response("The submitted hostname is same as current. Submit different hostname.")
            self.hostname_input.set_edit_text("")
            return
        try:
            # Attempt to set the new hostname
            subprocess.run(f"sudo hostnamectl set-hostname {new_hostname}", shell=True, check=True)
            logger.info(f"Hostname changed to: {new_hostname}")
            # Update the current hostname and display it
            self.current_hostname = new_hostname
            # Display success message
            response_message = (
                f"Hostname is changed to: {new_hostname}."
                f"{' Click next to proceed.' if self.setup_wizard else ''}"
            )
            self.display_response(response_message)
        except subprocess.CalledProcessError as e:
            # Display error message
            logger.error(f"Failed to set hostname: {e}")
            self.display_response(f"Failed to change hostname: {e}")
        # Clear the input field
        self.hostname_input.set_edit_text("")

    def clear_response(self):
        """
        Clears any previous response message.
        """
        self.response_widget.set_text("")

    def display_response(self, message: str):
        """
        Displays a response message in the UI.
        """
        self.response_widget.set_text(message)

    def reboot_system(self, button: urwid.Button) -> None:
        """
        Handles the logic for rebooting the system.
        """
        logging.debug('Reboot button clicked')
        try:
            subprocess.run("sudo reboot", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reboot: {e}")
            response_text = urwid.Text(f"Failed to reboot system: {e}")
            self.pile.contents.insert(1, (urwid.AttrMap(response_text, None), ('pack', None)))

    def exit_to_menu(self, button: urwid.Button) -> None:
        """
        Exits the hostname manager and emits the close signal.
        """
        logging.debug('Back button clicked, restarting layout')
        self.create_layout()
        self._emit('close')
