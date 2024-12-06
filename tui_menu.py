from __future__ import annotations
import urwid
import typing
import logging
from .loop import set_main_loop
from .PopUpFrame import PopUpFrame

logger = logging.getLogger(__name__)

main_loop = None

if typing.TYPE_CHECKING:
    from collections.abc import Hashable

class ActionDisplayNode(urwid.TreeWidget):
    unexpanded_icon = urwid.SelectableIcon("*", 0)
    expanded_icon = urwid.SelectableIcon("*", 0)

    def get_display_text(self) -> str | tuple[Hashable, str] | list[str | tuple[Hashable, str]]:
        return self.get_node().get_value()['name']

    def selectable(self) -> bool:
        return True

    def __init__(self, node: urwid.TreeNode):
        super().__init__(node)
        self.is_leaf = True
        self.expanded = False
        self._innerwidget = self.get_indented_widget()

    # refactored in order to limit the number of return statements to a maximum of three
    def keypress(self, size: tuple[int] | tuple[()], key: str) -> str | None:
        logger.debug(f"Keypress detected: {key}")
        if key == 'enter':
            action = self.get_node().get_value()["action"]
            logger.debug(f"Action retrieved: {action}")
            if callable(action):
                try:
                    logger.debug("Executing callable action.")
                    action()
                except Exception as e:
                    logging.error(f"Error calling action: {e}")
                return None
            if isinstance(action, urwid.Widget):
                launcher: PopUpFrame = self.get_node().poplaunch
                urwid.connect_signal(action, 'close', lambda button: launcher.close_pop_up())
                if hasattr(action, 'start') and callable(action.start):
                    logger.debug("Calling start method on action.")
                    try:
                        action.start()
                    except Exception as e:
                        logging.error(f"Error starting action: {e}")
                        return None
                launcher.open_pop_up(action)
                logger.debug("Popup launched with widget action.")
                return None

        return super().keypress(size, key)


class MenuDisplayNode(urwid.TreeWidget):
    def __init__(self, node: urwid.TreeNode):
        super().__init__(node)

    def get_display_text(self) -> str | tuple[Hashable, str] | list[str | tuple[Hashable, str]]:
        return self.get_node().get_value()['name']

class ActionNode(urwid.ParentNode):
    def __init__(
        self,
        value: typing.Any,
        poplaunch: urwid.PopUpLauncher,
        parent: urwid.ParentNode | None = None,
        key: typing.Hashable = None,
        depth: int | None = None
    ) -> None:
        super().__init__(value, parent, key, depth)
        self.poplaunch = poplaunch

    def load_widget(self) -> MenuDisplayNode:
        return ActionDisplayNode(self)

    def load_child_keys(self) -> typing.Sequence[typing.Hashable]:
        return []

class MenuNode(urwid.TreeNode):
    def __init__(
        self,
        value: typing.Any,
        poplaunch: urwid.PopUpLauncher,
        parent: urwid.ParentNode | None = None,
        key: typing.Hashable | None = None,
        depth: int | None = None
    ) -> None:
        super().__init__(value, parent, key, depth)
        self.poplaunch = poplaunch

    def load_widget(self) -> MenuDisplayNode:
        return MenuDisplayNode(self)

class MenuParentNode(urwid.ParentNode):
    def __init__(
        self,
        value: typing.Any,
        poplaunch: urwid.PopUpLauncher,
        parent: urwid.ParentNode | None = None,
        key: typing.Hashable = None,
        depth: int | None = None
    ) -> None:
        super().__init__(value, parent, key, depth)
        self.poplaunch = poplaunch

    def load_widget(self) -> MenuDisplayNode:
        return MenuDisplayNode(self)

    def load_child_keys(self):
        data = self.get_value()
        return range(len(data["children"]))

    def load_child_node(self, key) -> MenuParentNode | MenuNode:
        child_data = self.get_value()["children"][key]
        child_depth = self.get_depth() + 1
        logger.debug(f"Loading child node with data: {child_data}, depth: {child_depth}")
        if "children" in child_data:
            childclass = MenuParentNode
        elif "action" in child_data:
            childclass = ActionNode
        else:
            childclass = MenuNode
        return childclass(child_data, self.poplaunch, parent=self, key=key, depth=child_depth)

class Menu:
    palette: typing.ClassVar[tuple[str, str, str, ...]] = [
        ("body", "black", "light gray"),
        ("focus", "light gray", "dark blue", "standout"),
        ("head", "yellow", "black", "standout"),
        ("foot", "light gray", "black"),
        ("key", "light cyan", "black", "underline"),
        ("title", "white", "black", "bold"),
        ("flag", "dark gray", "light gray"),
        ("error", "dark red", "light gray"),
        (None, "light gray", "black"),
        ("heading", "black", "light gray"),
        ("header", "white", "dark red", "bold"),
        ("line", "black", "light gray"),
        ("options", "dark gray", "black"),
        ("focus heading", "white", "dark red"),
        ("focus line", "black", "dark red"),
        ("focus options", "black", "light gray"),
        ("selected", "white", "dark blue"),
        ("popbg", "white", "dark gray"),
        ("selectable", "white", "dark blue"),
        # Normal state for text editor
        ("editbox", "white", "dark blue"),
        # Focused state for text editor
        ("editbox_focus", "white", "dark green"),
        # Selectable items (like buttons)
        ("selectable", "white", "dark red"),
        # Response message styling
        ("response", "light gray", "black"),
    ]

    def __init__(self, data=None) -> None:
        logger.debug("Initializing Menu with data: %s", data)
        self.header = urwid.Text("Welcome to Catena")
        self.frame = urwid.Frame(
            urwid.Text(''),
            header=urwid.AttrMap(self.header, 'head'),
        )
        self.view = PopUpFrame(self.frame)
        self.topnode = MenuParentNode(data, self.view)
        logging.debug(f"Menu Parent Node: {self.topnode}")

        self.listbox = urwid.TreeListBox(urwid.TreeWalker(self.topnode))
        self.listbox.offset_rows = 1
        self.frame._body = urwid.AttrMap(self.listbox, 'body')
        self.frame._invalidate()
        logging.debug('Menu initialized and ready')

    def main(self) -> None:
        """Run the program."""
        logger.debug("Starting main loop.")
        self.loop = urwid.MainLoop(self.view, self.palette, pop_ups=True, unhandled_input=self.unhandled_input)
        # Register the main loop global - used by the terminal widgets
        set_main_loop(self.loop)
        self.loop.run()
        logging.debug('Main loop started')

    def unhandled_input(self, k: str | tuple[str, int, int, int]) -> None:
        if k in {"q", "Q"}:
            raise urwid.ExitMainLoop()
