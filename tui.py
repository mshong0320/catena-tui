#!/usr/bin/env python3

from __future__ import annotations
from .tui_menu import Menu
from .NetworkSelector import NetworkSelector
from .TerminalAction import TerminalAction
from .RawTerminalAction import RawTerminalAction
from .CommandAction import CommandAction
from .HostnameManager import HostnameManager
from .TimezoneManager import TimezoneManager
from .TimeManager import TimeManager
from .SetupWizard import SetupWizard
import subprocess
from dotenv import dotenv_values
import urwid
import logging
logger = logging.getLogger(__name__)


focus_map = {"heading": "focus heading", "options": "focus options", "line": "focus line"}

menu = {
    "name": 'Catena',
    "children": [
        {
            "name": "Networks",
            "children": [
                {
                    "name": "Network Interfaces",
                    "action": NetworkSelector()
                },
                {
                    "name": "Edit Network Settings",
                    "action": RawTerminalAction(['sudo', '/usr/bin/nmtui']),
                },
            ]
        },
        {
            "name": "Utilities",
            "children": [
                {
                    "name": "Configure System Host",
                    "action": HostnameManager()
                },
                {
                    "name": "Configure System Timezone",
                    "action": TimezoneManager()
                },
                {
                    "name": "Configure System Time",
                    "action": TimeManager()
                },
                {
                    "name": "System Information",
                    "action": CommandAction(['catena-info'], 'System Information')
                },
                {
                    "name": "Reboot",
                    "action": RawTerminalAction(['sudo', 'reboot'])
                },
                {
                    "name": "Shutdown",
                    "action": RawTerminalAction(['sudo', 'shutdown'])
                },
                {
                    "name": "Setup Wizard",
                    "action": SetupWizard()
                }
            ]
        }
    ]
}

menuClass = None

def check_network_interfaces():
    """
    Checks for network interfaces that follow the default ethernet naming convention
    (e.g., "eth0").

    Returns:
        bool: True if at least one interface starts with "eth", False otherwise.

    Logs:
        Prints error messages if the subprocess fails to run.
    """
    try:
        # Load the contents of the file using dotenv
        network_ports = dotenv_values("/etc/procentric/network_ports")
        # Iterate over the keys/values to check if 'eth' exists
        return any("eth" in x for x in network_ports.values())
    except subprocess.CalledProcessError as e:
        logging.debug(f"Error checking network ports file: {e}")
        return False
    except FileNotFoundError:
        logging.debug(f"File /etc/procentric/network_ports not found.")
        return False

def main() -> None:
    """
    The main function for launching the TUI application.
    Handles both the initial setup wizard and the main menu.
    """
    global menuClass
    menu_instance = Menu(menu)
    if check_network_interfaces():
        logging.debug("Default ethernet configuration with wrong port name detected. Launching SetupWizard")
        setup_wizard = SetupWizard(initial_setup=True)
        menu_instance.view = setup_wizard
        menu_instance.main()
    else:
        menu_instance.main()


if __name__ == "__main__":
    main()
