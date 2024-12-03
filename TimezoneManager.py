"""
TimezoneManager Module

This module contains the `TimezoneManager` class which is responsible for managing the system's timezone configuration.
It allows users to view the current timezone, select a new timezone, and set it using system commands. It also provides
options to reboot the system or return to the main menu.

Key Features:
-Displays the current system timezone.
-Allows users to select a new timezone via `tzselect`.
-Provides buttons for rebooting the system or returning to the main menu.
-Supports both initial and post-setup modes.
-Handles errors in the timezone selection and system reboot process.

Dependencies:
-`urwid`: For building the user interface.
-`subprocess`: For executing system commands to check and set the timezone.
-`logging`: For logging information and errors.
"""

import urwid
import subprocess
import logging
import typing
from .loop import get_main_loop

class TimezoneManager(urwid.WidgetWrap):
	"""
	A class that provides the functionality to manage and set the system's timezone.

	Attributes:
		signals (list): A list of signals the widget can emit. In this case, it supports the "close" signal.
		current_timezone (str): The current system timezone.
		current_timezone_show (urwid.Text): Widget displaying the current timezone.
		current_timezone_padded (urwid.Padding): Padded widget to center the current timezone display.
		select_timezone_button (urwid.Button): Button to allow the user to select a new timezone.
		selectTimezoneWrapped (urwid.Padding): Wrapped and padded button for selecting the timezone.
		reboot_button (urwid.Button): Button to trigger a system reboot.
		back_button (urwid.Button): Button to return to the main menu.
		backWrapped (urwid.Padding): Padded button for the back action.
		rebootWrapped (urwid.Padding): Padded button for the reboot action.
		initial_setup (bool): A flag to determine whether the wizard is in its initial setup state.

	Methods:
		__init__(initial_setup: bool): Initializes the TimezoneManager and sets up the UI layout.
		get_current_timezone(): Retrieves the current system timezone using `timedatectl`.
		create_layout(): Creates and configures the layout of the UI based on whether it's in initial setup mode.
		select_timezone(button): Handles the selection of a new timezone and updates the system timezone.
		reset_layout(): Updates the layout after setting a new timezone and displays relevant information.
		reboot_system(button): Reboots the system using a system command.
		exit_to_menu(button): Closes the current widget and returns to the main menu.
	"""

	signals: typing.ClassVar[list[str]] = ["close"]

	def __init__(self, setup_wizard: bool = False):
		logging.debug('Initializing TimezoneManager')
		self.current_timezone = self.get_current_timezone()
		self.current_timezone_show = urwid.Text(f"Current Timezone: {self.current_timezone}")
		self.current_timezone_padded = urwid.Padding(self.current_timezone_show, 'center', width=('relative', 50))
		self.select_timezone_button = urwid.Button("Set Timezone", on_press=self.select_timezone)
		self.selectTimezoneWrapped = urwid.Padding(urwid.AttrMap(self.select_timezone_button, 'selectable'), 'left', 20)
		self.reboot_button = urwid.Button("Reboot", self.reboot_system)
		self.back_button = urwid.Button("Back", self.exit_to_menu)
		self.backWrapped = urwid.Padding(urwid.AttrMap(self.back_button, 'selectable'), 'left', 20)
		self.rebootWrapped = urwid.Padding(urwid.AttrMap(self.reboot_button, 'selectable'),'left', 20)
		self.setup_wizard = setup_wizard
		self.create_layout()
		logging.debug('TimezoneManager initialized')

	def get_current_timezone(self):
		"""
		Retrieves the current system timezone using the `timedatectl` command.

		Returns:
			str: The current system timezone (e.g., "America/New_York"),
			or an error message if unable to determine the timezone.
		"""
		try:
			result = subprocess.run(['timedatectl', 'show', '--property=Timezone'], capture_output=True, text=True, check=True)
			timezone_name = result.stdout.strip().split('=')[-1]
		except (subprocess.CalledProcessError, FileNotFoundError, OSError):
			timezone_name = "Failed to Determine Timezone"
		return timezone_name

	def create_layout(self):
		"""
		Creates the layout for the TimezoneManager based on whether it's in initial setup mode or not.
		In initial setup mode, only the current timezone and selection button are shown. In non-initial setup mode,
		the layout also includes the option to reboot and return to the main menu.
		"""
		# Common elements
		self.pile = urwid.Pile([
			self.current_timezone_padded,
			urwid.Divider(),
			self.selectTimezoneWrapped,
			])
		# Additional elements only if initial_setup is None
		if not self.setup_wizard:
			self.pile.contents.append((self.backWrapped, ('pack', None)))
			self.pile.contents.append((self.rebootWrapped, ('pack', None)))
		# Set the pile and wrap it in a LineBox
		self.box = urwid.LineBox(urwid.Filler(self.pile, valign='top'), title="Configure Timezone")
		super().__init__(self.box)

	def select_timezone(self, button):
		"""
		Allows the user to select a new timezone using `tzselect` and updates the system timezone.
		This method halts the main loop, runs the `tzselect` command to select the timezone, and applies the
		selected timezone using `timedatectl`. Afterward, the layout is updated to reflect the change.
		"""
		try:
			main_loop = get_main_loop()
			main_loop.screen.stop()
			tz_output = subprocess.check_output(['tzselect'])
			selected_timezone = tz_output.splitlines()[-1].strip()
			subprocess.check_call(['sudo', 'timedatectl', 'set-timezone', selected_timezone])
			self.current_timezone = self.get_current_timezone()
		except subprocess.CalledProcessError as e:
			logging.error(f"Failed to set timezone: {e}")
			error_text = urwid.Text(f"Error setting timezone: {e}")
			self.pile.contents.append((error_text, ('pack', None)))
		finally:
			main_loop.screen.start()
			self.reset_layout()

	def reset_layout(self, *args):
		"""
		Resets the layout to reflect the updated timezone and provides feedback to the user.
		Displays a success message with the current timezone and updates the layout. If it's not in initial
		setup mode, the Reboot and Back buttons are shown; otherwise, the Next button is displayed.
		"""
		self.pile.contents.clear()
		self.current_timezone = self.get_current_timezone()
		if not self.setup_wizard:
			success_message = urwid.Text(f"Timezone is set to {self.current_timezone}. Please reboot to apply changes.")
		else:
			success_message = urwid.Text(f"Timezone is set to {self.current_timezone}. Please click Next to proceed.")
		success_message_padded = urwid.Padding(success_message, 'center', width=('relative', 50))
		self.current_timezone_show.set_text(f"Current Timezone: {self.current_timezone}")
		new_pile_content = [
							urwid.Text(""),
							self.current_timezone_padded,
							urwid.Text(""),
							success_message_padded,
							urwid.Text(""),
							self.selectTimezoneWrapped,
							]
		self.pile.contents.extend([(widget, ('pack', None)) for widget in new_pile_content])
		if not self.setup_wizard:
			self.pile.contents.append((self.backWrapped, ('pack', None)))
			self.pile.contents.append((self.rebootWrapped, ('pack', None)))

	def reboot_system(self, button):
		try:
			subprocess.run("sudo reboot", shell=True, check=True)
		except subprocess.CalledProcessError as e:
			response_text = urwid.Text(f"Failed to reboot system: {e}")
			self.pile.contents.insert(1, (urwid.AttrMap(response_text, None), ('pack', None)))

	def exit_to_menu(self, button):
		"""
		Exits the current wizard and returns to the main menu.
		This method emits the "close" signal and resets the layout.
		"""
		self._emit('close')
		self.create_layout()
