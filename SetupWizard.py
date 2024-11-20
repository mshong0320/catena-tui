"""
This module contains the `SetupWizard` class that provides an interactive setup wizard for configuring
system settings during the initial setup phase. The wizard guides the user through setting up the hostname,
timezone, system time, and network configuration.
The setup wizard automatically triggers if any network interface does not follow the expected naming convention
(for example, if the interface name does not start with 'eno').

Module Components:
- `SetupWizard`: A class that defines the setup wizard, including the steps for configuring system settings.
- `update_body`: A method to update the body of the wizard with the current step.
- `next_step`: A method to advance to the next step in the wizard.
- `back`: A method to show the completion screen when setup is finished.
- `reboot_system`: A method that reboots the system after the setup is complete.
- `finish`: A method to finish the setup and close the wizard.

Dependencies:
- `urwid`: A terminal UI library for creating and managing the wizard's interface.
- `logging`: Used for logging the setup process for debugging and record-keeping.
- `subprocess`: Used for running shell commands to get network interface data and reboot the system.

The wizard will go through the following steps in sequence:
1. Set Hostname
2. Set Timezone
3. Set Time
4. Configure Network

The setup wizard's interface is implemented using `urwid`'s widget system, and the UI consists of buttons,
form fields, and dividers to guide the user through each setup step.

The wizard can be automatically triggered if certain conditions are met, such as an unexpected network interface name
being detected. The user can also manually trigger the setup if needed.

Example usage:
    setup_wizard = SetupWizard()
    mainloop = urwid.MainLoop(setup_wizard)
    mainloop.run()
"""

import urwid
import logging
import typing
import subprocess
from .PopUpFrame import PopUpFrame
from .HostnameManager import HostnameManager
from .TimezoneManager import TimezoneManager
from .TimeManager import TimeManager
from .NetworkSelector import NetworkSelector
from .loop import get_main_loop

logging.basicConfig(
    filename='setup_wizard.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SetupWizard(urwid.WidgetWrap):
    """
    A class representing the setup wizard used to configure system settings during initial setup.

    This wizard guides the user through a series of steps to configure the system, including:
    - Setting the hostname
    - Setting the timezone
    - Setting the time
    - Configuring network settings

    Attributes:
        steps (list): A list of tuples representing each step in the setup wizard.
        current_step_index (int): Index of the current step being displayed.
        next_button (urwid.Button): The "Next" button to navigate between steps.
        pile (urwid.Pile): A container to hold the widgets in the setup wizard.
        _w (urwid.LineBox): The main widget containing the setup wizard's UI elements.
    """

    signals: typing.ClassVar[list[str]] = ["close"]

    def __init__(self, initial_setup: bool = False):
        logging.debug("Initializing SetupWizard")
        self.initial_setup = initial_setup
        self.steps = [
            ("Set Hostname", HostnameManager(initial_setup=initial_setup)),
            ("Set Timezone", TimezoneManager(initial_setup=initial_setup)),
            ("Set Time", TimeManager(initial_setup=initial_setup)),
            ("Configure Network", NetworkSelector(initial_setup=initial_setup))
        ]
        self.current_step_index = 0
        self.next_button = urwid.Button("Next", self.next_step)
        self.next_button_wrapped = urwid.Padding(urwid.AttrMap(self.next_button, 'selectable'), 'left', 12)
        self.pile = urwid.Pile([
            self.next_button_wrapped
        ])
        self._w = urwid.LineBox(urwid.Filler(self.pile), title="Setup Wizard")
        super().__init__(self._w)
        self.update_body()
        logging.debug("Initialized SetupWizard with LineBox layout.")

    def update_body(self):
        """
        Updates the body of the setup wizard to display the current step.
        Displays the step's name and widget, and sets the layout for the current step. If the step is the
        NetworkSelector, it will show the pop-up frame for network configuration.
        """
        try:
            step_name, step_widget = self.steps[self.current_step_index]
            logging.debug(f"Updating body with step: {step_name}")
            if isinstance(step_widget, NetworkSelector):
                urwid.connect_signal(step_widget, "close", self.back)
                self._w = PopUpFrame(step_widget)
                self._invalidate()
            else:
                self.pile.contents.clear()
                self.pile.contents.extend([
                    (step_widget, self.pile.options()),
                    (urwid.Divider(), self.pile.options()),
                    (self.next_button_wrapped, self.pile.options())
                ])
        except ValueError as e:
            logging.error(f"ValueError in update_body: {e}")
            logging.debug(f"Steps: {self.steps}, Current step index: {self.current_step_index}")

    def next_step(self, button):
        """
        Handles the "Next" button click event, advancing to the next step in the wizard.
        If there are more steps, the wizard moves to the next step. If the last step is reached,
        it displays a "Finish" button.
        """
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            logging.debug(f"Moving to next step index: {self.current_step_index}")
            self.update_body()

    def back(self, button):
        """
        Handles the "Back" button click event, displaying the completion screen with
        options to finish or reboot the system.
        """
        if self.initial_setup:
            reboot_button = urwid.Button("Reboot", self.reboot_system)
            completion_message = urwid.Text("Setup is now complete. Please reboot to apply the changes made")
            reboot_button_wrapped = urwid.Padding(urwid.AttrMap(reboot_button, 'selectable'), 'left', 12)
            completion_message_wrapped = urwid.Padding(completion_message, 'center', width=('relative', 50))
            self.pile.contents.clear()
            self.pile.contents.extend([
                                        (completion_message_wrapped, self.pile.options()),
                                        (urwid.Divider(), self.pile.options()),
                                        (reboot_button_wrapped, self.pile.options())
                                    ])
        else:
            finish_button = urwid.Button("Home", self.finish)
            reboot_button = urwid.Button("Reboot", self.reboot_system)
            completion_message = urwid.Text("Setup is now complete. Please reboot now or later")
            finish_button_wrapped = urwid.Padding(urwid.AttrMap(finish_button, 'selectable'), 'left', 12)
            reboot_button_wrapped = urwid.Padding(urwid.AttrMap(reboot_button, 'selectable'), 'left', 12)
            completion_message_wrapped = urwid.Padding(completion_message, 'center', width=('relative', 50))
            self.pile.contents.clear()
            self.pile.contents.extend([
                                    (completion_message_wrapped, self.pile.options()),
                                    (urwid.Divider(), self.pile.options()),
                                    (finish_button_wrapped, self.pile.options()),
                                    (urwid.Divider(), self.pile.options()),
                                    (reboot_button_wrapped, self.pile.options())
                                ])
        self._w = urwid.LineBox(urwid.Filler(self.pile), title="Setup Wizard Completion")
        self._invalidate()
        logging.debug("Displayed setup completion screen.")

    def reboot_system(self, button):
        """
        Reboots the system.
        This method is called when the user selects the "Reboot" button at the end of the setup wizard.
        """
        try:
            subprocess.run("sudo reboot", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            response_text = urwid.Text(f"Failed to reboot system: {e}")
            self.pile.contents.insert(1, (urwid.AttrMap(response_text, None), ('pack', None)))

    def finish(self, button):
        """
        Finishes the setup process and closes the setup wizard.
        This method is called when the user selects the "Finish" button at the end of the setup wizard.
        """
        self.current_step_index = 0
        self.update_body()
        self._emit('close')
        logging.debug("Finishing setup wizard and returning to homescreen")
