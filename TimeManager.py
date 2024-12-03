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
	"""
	A class that provides the functionality to manage and set the system's time.

	Methods:
		__init__(initial_setup: bool): Initializes the Timemanager and sets up the UI layout.
		get_current_timezone(): Retrieves the current system time using `timedatectl`.
		create_layout(): Creates and configures the layout of the UI based on whether it's in initial setup mode.
		submit(button): Handles the selection of a new time and updates the system time.
		reset_layout(): Updates the layout after setting a new timezone and displays relevant information.
		reboot_system(button): Reboots the system using a system command.
		exit_to_menu(button): Closes the current widget and returns to the main menu.
	"""
	signals: typing.ClassVar[list[str]] = ["close"]

	def __init__(self, setup_wizard: bool = False):
		"""
		Initialize the TimeManager class.

		Args:
			initial_setup (bool): Determines if the TimeManager operates in initial setup mode. Default is False.
		"""
		logging.debug('Initializing TimeManager')
		self.current_time = self.get_current_time()
		self.current_time_show = urwid.Text(f"Current Time: {self.current_time}")
		self.current_time_padded = urwid.Padding(self.current_time_show, 'center', width=('relative', 50))
		self.ntp_enabled = self.check_ntp_status()
		self.ntp_toggle = urwid.CheckBox("Enable NTP", state=self.ntp_enabled, on_state_change=self.toggle_ntp)
		self.ntp_toggle_padded = urwid.Padding(self.ntp_toggle, 'center', width=('relative', 50))
		self.reboot_button = urwid.Button("Reboot", self.reboot_system)
		self.back_button = urwid.Button("Back", self.exit_to_menu)
		self.backWrapped = urwid.Padding(urwid.AttrMap(self.back_button, 'selectable'), 'left', 20)
		self.rebootWrapped = urwid.Padding(urwid.AttrMap(self.reboot_button, 'selectable'), 'left', 20)
		self.time_input = urwid.Edit("Please enter new time (format: YYYY-MM-DD HH:MM:SS): ", edit_text="", multiline=False)
		self.time_input_wrapped = urwid.Pile([
			urwid.LineBox(
				urwid.Padding(
					urwid.AttrMap(self.time_input, "editbox", "editbox_focus"),
					align='center', width=('relative', 50)
				)
			)
		])
		self.submit_button = urwid.Button("Submit", on_press=self.submit)
		self.submit_button_wrapped = urwid.Padding(urwid.AttrMap(self.submit_button, 'selectable'), 'left', 20)
		self.setup_wizard = setup_wizard
		self.response_widget = urwid.Text("")
		self.response_widget_padded = urwid.Padding(self.response_widget, 'center', width=('relative', 50))
		self.create_layout()
		self.time_input.set_edit_text(self.current_time)
		logging.debug('TimeManager initialized')

	def check_ntp_status(self) -> bool:
		"""
		Checks if NTP is currently enabled on the system by parsing the output of `timedatectl`.
		"""
		try:
			# filters output to only the NTP property
			result = subprocess.run(
				["timedatectl", "show", "--property=NTP"],
				capture_output=True, text=True, check=True
			)
			# Parse the output to extract the NTP value. Checks whether the value is yes (indicating NTP is enabled)
			output = result.stdout.strip()
			if output.startswith("NTP="):
				ntp_status = output.split("=")[1].strip().lower()
				return ntp_status == "yes"
			else:
				logging.error("Unexpected output format from `timedatectl show`: %s", output)
				return False
		except subprocess.CalledProcessError as e:
			logging.error(f"Failed to check NTP status: {e}")
			return False

	def toggle_ntp(self, checkbox: urwid.CheckBox, state: bool) -> None:
		"""
		Updates the internal NTP state without applying changes.

		Args:
			checkbox: The checkbox triggering this action.
			state (bool): The new state of the checkbox.
		"""
		self.ntp_enabled = state
		self.display_response(f"NTP status set to {'enabled' if state else 'disabled'} (Pending Submit).")

	def apply_ntp_status(self):
		"""
		Apply the NTP synchronization status based on the checkbox state.
		"""
		subprocess.run(
			["sudo", "timedatectl", "set-ntp", "true" if self.ntp_enabled else "false"],
			check=True
		)
		ntp_status = "enabled" if self.ntp_enabled else "disabled"
		logging.info(f"NTP synchronization {ntp_status}.")
		self.display_response(f"NTP synchronization {ntp_status} applied.")

	def process_manual_time_entry(self):
		"""
		Process and apply the manually entered system time.
		"""
		new_time = self.time_input.edit_text.strip()
		# Validate the time format
		datetime.strptime(new_time, "%Y-%m-%d %H:%M:%S")
		# Set the system time
		subprocess.run(['sudo', 'timedatectl', 'set-time', new_time], check=True)
		self.current_time = new_time
		self.current_time_show.set_text(f"Current Time: {self.current_time}")
		logging.info(f"System time updated to: {self.current_time}")
		response_msg = (
			f"Time successfully changed to {self.current_time}. "
			f"{'Click next to proceed.' if self.setup_wizard else 'Please reboot.'}"
		)
		self.display_response(response_msg)

	def handle_error(self, error_message):
		"""
		Handle and display error messages.

		Args:
		error_message (str): The error message to display.
		"""
		self.display_response(error_message)

	def clear_time_input_if_needed(self):
		"""
		Clear the time input field if NTP is disabled.
		"""
		if not self.ntp_enabled:
			self.time_input.set_edit_text("")

	def submit(self, button):
		"""
		Handles submission of NTP and system time updates.

		Args:
		button: The button triggering this action.
		"""
		# Clear any existing response message
		self.clear_response()
		try:
			# Apply NTP status
			self.apply_ntp_status()
			# Handle manual time entry if NTP is disabled
			if not self.ntp_enabled:
				self.process_manual_time_entry()
		except ValueError:
			self.handle_error("Failed to set time: Invalid format. Use YYYY-MM-DD HH:MM:SS.")
		except subprocess.CalledProcessError as e:
			self.handle_error(f"Error updating system settings: {e}")
		finally:
			self.clear_time_input_if_needed()

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

	def clear_response(self):
		"""
		Clears any previous response message.
		"""
		self.response_widget.set_text("")

	def display_response(self, message: str) -> None:
		"""
		Displays a response message in the UI.
		"""
		self.response_widget.set_text(message)

	def create_layout(self):
		"""
		Create the initial layout of the TimeManager UI.
		"""
		self.pile = urwid.Pile([
			self.current_time_padded,
			urwid.Divider(),
			self.ntp_toggle_padded,
			urwid.Divider(),
			self.response_widget_padded,
			urwid.Divider(),
		])

		self.pile.contents.insert(0, (self.time_input_wrapped, ('pack', None)))
		self.pile.contents.append((self.submit_button_wrapped, ('pack', None)))

		# Additional elements only if initial_setup is None
		if not self.setup_wizard:
			self.pile.contents.append((self.backWrapped, ('pack', None)))
			self.pile.contents.append((self.rebootWrapped, ('pack', None)))

		self.box = urwid.LineBox(urwid.Filler(self.pile, valign='top'), title="Configure Time")
		super().__init__(self.box)

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
		self.create_layout()
		self._emit('close')
