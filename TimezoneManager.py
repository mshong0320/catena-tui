import urwid
import subprocess
import logging
import typing
from .loop import get_main_loop

class TimezoneManager(urwid.WidgetWrap):
	signals: typing.ClassVar[list[str]] = ["close"]

	def __init__(self, initial_setup: bool = True) -> None:
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
		self.initial_setup = initial_setup
		self.create_layout()
		logging.debug('TimezoneManager initialized')

	def get_current_timezone(self):
		try:
			result = subprocess.run(['timedatectl', 'show', '--property=Timezone'], capture_output=True, text=True, check=True)
			timezone_name = result.stdout.strip().split('=')[-1]
		except (subprocess.CalledProcessError, FileNotFoundError, OSError):
			timezone_name = "Failed to Determine Timezone"
		return timezone_name

	def create_layout(self):
		if self.initial_setup:
			self.pile = urwid.Pile([
							self.current_timezone_padded,
							urwid.Divider(),
							self.selectTimezoneWrapped,
							urwid.Divider(),
							self.backWrapped,
							urwid.Divider(),
							self.rebootWrapped
						])
			self.pile.contents[-1] = (urwid.Text(''), ('pack', None))  # Hide the Reboot button initially
		else:
			self.pile = urwid.Pile([
							self.current_timezone_padded,
							urwid.Divider(),
							self.selectTimezoneWrapped,
						])
		self.box = urwid.LineBox(urwid.Filler(self.pile, valign='top'), title="Configure Timezone")
		super().__init__(self.box)

	def select_timezone(self, button):
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
		self.pile.contents.clear()
		self.current_timezone = self.get_current_timezone()
		if self.initial_setup:
			success_message = urwid.Text(f"Timezone is successfully set to {self.current_timezone}. Please reboot to apply the changes.")
		else:
			success_message = urwid.Text(f"Timezone is successfully set to {self.current_timezone}. Please click Next button below to proceed.")
		success_message_padded = urwid.Padding(success_message, 'center', width=('relative', 50))
		self.current_timezone_show.set_text(f"Current Timezone: {self.current_timezone}")
		if self.initial_setup:
			new_pile_content = [	
								urwid.Text(""),
								self.current_timezone_padded,
								urwid.Text(""),
								success_message_padded,
								urwid.Text(""),
								self.selectTimezoneWrapped,
								urwid.Text(""),
								self.backWrapped,
								urwid.Text(""),
								self.rebootWrapped
							]
			self.pile.contents.extend([(widget, ('pack', None)) for widget in new_pile_content])
		else:
			new_pile_content = [	
								urwid.Text(""),
								self.current_timezone_padded,
								urwid.Text(""),
								success_message_padded,
								urwid.Text(""),
								self.selectTimezoneWrapped,
							]
			self.pile.contents.extend([(widget, ('pack', None)) for widget in new_pile_content])

	def reboot_system(self, button):
		try:
			subprocess.run("sudo reboot", shell=True, check=True)
		except subprocess.CalledProcessError as e:
			response_text = urwid.Text(f"Failed to reboot system: {e}")
			self.pile.contents.insert(1, (urwid.AttrMap(response_text, None), ('pack', None)))

	def exit_to_menu(self, button):
		self._emit('close')
		self.reset_layout()