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
    signals: typing.ClassVar[list[str]] = ["close"]

    def __init__(self, initial_setup: bool = False):
        logging.debug("Initializing SetupWizard")
        self.initial_setup = initial_setup
        self.steps = [
            ("Set Hostname", HostnameManager(initial_setup=False)),
            ("Set Timezone", TimezoneManager(initial_setup=False)),
            ("Set Time", TimeManager(initial_setup=False)),
            ("Configure Network", NetworkSelector(initial_setup=True))
        ]
        self.current_step_index = 0
        self.next_button = urwid.Button("Next", self.next_step)
        self.next_button_wrapped = urwid.Padding(urwid.AttrMap(self.next_button, 'selectable'), 'left', 12)
        self.pile = urwid.Pile([
            self.next_button_wrapped
        ])
        self._w = urwid.LineBox(urwid.Filler(self.pile), title="Setup Wizard")
        super().__init__(self._w)
        #self.check_and_start_if_needed()
        self.update_body()     # Update the body with the first step
        logging.debug("Initialized SetupWizard with LineBox layout.")

    def update_body(self):
        try:
            step_name, step_widget = self.steps[self.current_step_index]
            logging.debug(f"Updating body with step: {step_name}")
            if isinstance(step_widget, NetworkSelector):
                urwid.connect_signal(step_widget, "close", self.back)
                self._w = PopUpFrame(step_widget)
                self._invalidate()
            else:
                self.pile.contents.clear()  # Clear previous contents
                self.pile.contents.extend([
                    (step_widget, self.pile.options()),
                    (urwid.Divider(), self.pile.options()),
                    (self.next_button_wrapped, self.pile.options())
                ])
        except ValueError as e:
            logging.error(f"ValueError in update_body: {e}")
            logging.debug(f"Steps: {self.steps}, Current step index: {self.current_step_index}")

    def next_step(self, button):
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            logging.debug(f"Moving to next step index: {self.current_step_index}")
            self.update_body()
            
    def back(self, button):
        self._w.close_pop_up()
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
            completion_message = urwid.Text("Setup is now complete. Please reboot to apply the changes made")
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
        self._invalidate()  # Refresh the display
        logging.debug("Displayed setup completion screen.")   

    def reboot_system(self, button):
        try:
            subprocess.run("sudo reboot", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            response_text = urwid.Text(f"Failed to reboot system: {e}")
            self.pile.contents.insert(1, (urwid.AttrMap(response_text, None), ('pack', None)))

    def finish(self, button):
        self.current_step_index = 0
        self.update_body()
        self._emit('close')
        logging.debug("Finishing setup wizard and returning to homescreen")
