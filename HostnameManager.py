import urwid
import subprocess
import logging
import typing
import platform
logger = logging.getLogger(__name__)


class HostnameManager(urwid.WidgetWrap):
    signals: typing.ClassVar[list[str]] = ["close"]

    def __init__(self, initial_setup: bool = True) -> None:
        logging.debug('Initializing HostnameManager')
        self.initial_setup = initial_setup
        self.create_layout()
        logging.debug('HostnameManager initialized')

    def create_layout(self):
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
        
        if self.initial_setup:
            self.pile = urwid.Pile([
                self.hostname_input_padded,
                urwid.Divider(),
                self.current_hostname_padded,
                urwid.Divider(),
                self.submitWrapped,
                self.backWrapped,
                self.rebootWrapped  # Reboot button fixed in place, but hidden initially
            ])
            self.pile.contents[-1] = (urwid.Text(''), ('pack', None))  # Hide the Reboot button initially
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
        logging.debug('Submit button clicked')
        new_hostname = self.hostname_input.get_edit_text().strip()
        logging.debug(f'New hostname input: {new_hostname}')
        if self.initial_setup:
            self.pile.contents = [
                (urwid.Padding(self.hostname_input, 'center', width=('relative', 50)), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (urwid.Padding(self.current_hostname_display, 'center', width=('relative', 50)), ('pack', None)),
                (urwid.Divider(), ('pack', None)),
                (self.submitWrapped, ('pack', None)),
                (self.backWrapped, ('pack', None)),
                (self.rebootWrapped, ('pack', None))  # Keep the Reboot button fixed below Back
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
                if self.initial_setup:
                    response_text = urwid.Text(f"Hostname has been changed to: {self.current_hostname}. Please reboot to apply the change.")
                else:
                    response_text = urwid.Text(f"Hostname has been changed to: {self.current_hostname}. Please click the Next button to proceed")
                response_text_padded = urwid.Padding(response_text, 'center', width=('relative', 50))
                self.pile.contents.insert(3, (urwid.AttrMap(response_text_padded, None), ('pack', None)))
                if not self.reboot_button_displayed and self.initial_setup:
                    self.pile.contents[-1] = (self.rebootWrapped, ('pack', None))  # Display Reboot button
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
