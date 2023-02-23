from abc import ABC, abstractmethod
from enum import Enum, auto

from text_trivia_maze_view import TextTriviaMazeView

_COMMAND_DESC_KEY = "description"
_COMMAND_KEY_KEY = "key"
_COMMAND_TYPE = "type"
_COMMAND_TYPE_OTHER = "other"
_COMMAND_TYPE_ITEM = "item"
_COMMAND_TYPE_MOVEMENT = "movement"


class TriviaMazeModelObserver(ABC):
    def __init__(self, maze_model):
        self._maze_model = maze_model

    @abstractmethod
    def update(self):
        pass


class TriviaMazeController(TriviaMazeModelObserver):
    @abstractmethod
    def process_keystroke(self, key):
        """
        Takes a keyboard input and interprets it as a command to be issued to
        the model or view which is then called as appropriate.
        """

    @abstractmethod
    def start_main_event_loop(self):
        """
        Display main menu and start listening for input from user
        """


class TextTriviaMazeController(TriviaMazeController):
    """
    Controls view and model based on keyboard input received by the view, as
    well as potentially information exposed by the model (e.g. if the model
    has a question and answer to be asked, the controller has the view ask it
    and get an answer.)
    """

    def __init__(self, maze_model):
        super().__init__(maze_model)

        # Create a view object
        dismiss_keys = (
            DismissibleCommandContext.COMMANDS[
                DismissibleCommandContext.Command.DISMISS
            ][_COMMAND_KEY_KEY],
        )
        self.__maze_view = TextTriviaMazeView(
            maze_model, self, "Trivia Maze", dismiss_keys
        )

        # Initialize command interpretation contexts
        self.__main_menu_context = MainMenuCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__main_help_menu_context = MainHelpMenuCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__primary_interface_context = PrimaryInterfaceCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__in_game_menu_context = InGameMenuCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__map_legend_menu_context = MapLegendCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__command_legend_menu_context = CommandLegendCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__game_won_menu_context = GameWonCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__game_lost_menu_context = GameLostCommandContext(
            self, self._maze_model, self.__maze_view
        )
        self.__question_and_answer_context = QuestionAndAnswerCommandContext(
            self, self._maze_model, self.__maze_view
        )

        # Player starts out at the main menu, so make that the active context.
        # NOTE: This sets the `__active_context` instance attr
        self.set_active_context("main_menu")

    def start_main_event_loop(self):
        self.__maze_view.mainloop()

    def process_keystroke(self, key):
        self.__active_context.process_keystroke(key)

    def get_active_context(self):
        return self.__active_context

    def set_active_context(self, context_specifier):
        if context_specifier == "main_menu":
            self.__active_context = self.__main_menu_context
        elif context_specifier == "main_help_menu":
            self.__active_context = self.__main_help_menu_context
        elif context_specifier == "primary_interface":
            self.__active_context = self.__primary_interface_context
        elif context_specifier == "in_game_menu":
            self.__active_context = self.__in_game_menu_context
        elif context_specifier == "map_legend_menu":
            self.__active_context = self.__map_legend_menu_context
        elif context_specifier == "command_legend_menu":
            self.__active_context = self.__command_legend_menu_context
        elif context_specifier == "game_won_menu":
            self.__active_context = self.__game_won_menu_context
        elif context_specifier == "game_lost_menu":
            self.__active_context = self.__game_lost_menu_context
        elif context_specifier == "question_and_answer":
            self.__active_context = self.__question_and_answer_context

    def update(self):
        # FIXME: Implement what should happen here when model changes

        # game_status = self._maze_model.get_game_status()
        # if game_status == "lose":
        # elif game_status == "win":
        pass


class CommandContext(ABC):
    """
    Interprets keystrokes within a specific context. For example, one context
    might be the main menu while one could be the primary game interface.
    """

    def __init__(self, maze_controller, maze_model, maze_view):
        self._maze_controller = maze_controller
        self._maze_model = maze_model
        self._maze_view = maze_view

    def __init_subclass__(cls, *args, **kwargs):
        """Force all subclasses to define a COMMANDS class attr"""
        super().__init_subclass__(*args, **kwargs)
        if not hasattr(cls, "COMMANDS"):
            raise TypeError(
                "Subclasses of {self.__class__.__name__} must define the COMMANDS class attr"
            )

    @abstractmethod
    def process_keystroke(self, key):
        """Interpret a keystroke and perform the relevant actions on the model
        and view based on the current context."""


class MenuCommandContext(CommandContext):
    class Command(Enum):
        """Enumeration used to fix commands to a small finite support set."""

        SELECT = auto()

    COMMANDS = {
        # Movement commands
        Command.SELECT: {
            _COMMAND_TYPE: _COMMAND_TYPE_OTHER,
            _COMMAND_DESC_KEY: "Select",
            _COMMAND_KEY_KEY: "Return",
        }
    }


class MainMenuCommandContext(MenuCommandContext):
    def process_keystroke(self, key):
        # NOTE: We ignore arrow keys here since the GUI is responsible for
        # having arrow keys traverse the menu. In fact, we actually only care
        # about the user hitting Return inside of this menu.
        if key != self.COMMANDS[self.Command.SELECT][_COMMAND_KEY_KEY]:
            return

        # Trigger the currently selected item in the main menu
        selected_option = self._maze_view.get_main_menu_current_selection()

        # NOTE: One might choose to have the controller tell the view what options
        # to add to the menu when it creates it in order to avoid duplication
        if selected_option == "Start game":
            # FIXME: Implement a difficulty selection and/or adventurer naming
            # menu and have the user go through that here. This may mean we
            # need to break up the stuff in the model's initialization so that
            # its __init__ doesn't really do anything.

            # Hide main menu so user can begin playing and switch contexts
            self._maze_view.hide_main_menu()

            self._maze_controller.set_active_context("primary_interface")

        elif selected_option == "Help":
            self._maze_view.show_main_help_menu()
            self._maze_controller.set_active_context("main_help_menu")

        elif selected_option == "Quit game":
            # Exit out of everything and close the window
            self._maze_view.quit_entire_game()


class InGameMenuCommandContext(MenuCommandContext):
    def process_keystroke(self, key):
        # NOTE: We ignore arrow keys here since the GUI is responsible for
        # having arrow keys traverse the menu. In fact, we actually only care
        # about the user hitting Return inside of this menu.
        if key != self.COMMANDS[self.Command.SELECT][_COMMAND_KEY_KEY]:
            return

        # Trigger the currently selected item in the main menu
        selected_option = (
            self._maze_view.get_in_game_menu_current_selection().lower()
        )

        # NOTE: One might choose to have the controller tell the view what options
        # to add to the menu when it creates it in order to avoid duplication
        if selected_option == "back to game":
            self._maze_view.hide_in_game_menu()
            self._maze_controller.set_active_context("primary_interface")

        elif selected_option == "display map legend":
            self._maze_view.show_map_legend_menu()
            self._maze_controller.set_active_context("map_legend_menu")

        elif selected_option == "display commands":
            # Generate legend symbols/descriptions to display
            # FIXME: Don't hard-code 'key' or 'description' here
            symbols = tuple(
                entry["key"]
                for entry in PrimaryInterfaceCommandContext.COMMANDS.values()
            )
            descriptions = tuple(
                entry["description"]
                for entry in PrimaryInterfaceCommandContext.COMMANDS.values()
            )

            self._maze_view.show_command_legend_menu(
                symbols, descriptions, num_cols=2
            )
            self._maze_controller.set_active_context("command_legend_menu")

        elif selected_option == "return to main menu":
            # Have the model create a completely new map and reset all item
            # counters to zero, etc.
            self._maze_model.reset()

            # Get rid of the in-game menu and put main menu over the top of the
            # reconstructed game
            self._maze_view.hide_in_game_menu()
            self._maze_view.show_main_menu()

            self._maze_controller.set_active_context("main_menu")

        elif selected_option == "quit game":
            # Exit out of everything and close the window
            self._maze_view.quit_entire_game()


class DismissibleCommandContext(CommandContext):
    class Command(Enum):
        """Enumeration used to fix commands to a small finite support set."""

        DISMISS = auto()

    COMMANDS = {
        # Movement commands
        Command.DISMISS: {
            _COMMAND_TYPE: _COMMAND_TYPE_OTHER,
            _COMMAND_DESC_KEY: "Dismiss",
            _COMMAND_KEY_KEY: "Return",
        }
    }


class MainHelpMenuCommandContext(DismissibleCommandContext):
    def process_keystroke(self, key):
        if key == self.COMMANDS[self.Command.DISMISS][_COMMAND_KEY_KEY]:
            self._maze_view.hide_main_help_menu()
            self._maze_controller.set_active_context("main_menu")


class MapLegendCommandContext(DismissibleCommandContext):
    def process_keystroke(self, key):
        if key == self.COMMANDS[self.Command.DISMISS][_COMMAND_KEY_KEY]:
            self._maze_view.hide_map_legend_menu()
            self._maze_controller.set_active_context("in_game_menu")


class CommandLegendCommandContext(DismissibleCommandContext):
    def process_keystroke(self, key):
        if key == self.COMMANDS[self.Command.DISMISS][_COMMAND_KEY_KEY]:
            self._maze_view.hide_command_legend_menu()
            self._maze_controller.set_active_context("in_game_menu")


class GameWonCommandContext(DismissibleCommandContext):
    def process_keystroke(self, key):
        if key == self.COMMANDS[self.Command.DISMISS][_COMMAND_KEY_KEY]:
            self._maze_view.hide_game_won_menu()
            self._maze_controller.set_active_context("main_menu")


class GameLostCommandContext(DismissibleCommandContext):
    def process_keystroke(self, key):
        if key == self.COMMANDS[self.Command.DISMISS][_COMMAND_KEY_KEY]:
            self._maze_view.hide_game_lost_menu()
            self._maze_controller.set_active_context("main_menu")


class PrimaryInterfaceCommandContext(CommandContext):
    class Command(Enum):
        """Enumeration used to fix commands to a small finite support set."""

        # Movement commands
        MOVE_EAST = auto()
        MOVE_NORTH = auto()
        MOVE_WEST = auto()
        MOVE_SOUTH = auto()

        # Item commands
        USE_HEALING_POTION = auto()
        USE_VISION_POTION = auto()

        # Other commands
        SHOW_IN_GAME_MENU = auto()
        QUIT_GAME = auto()

    COMMANDS = {
        # Movement commands
        Command.MOVE_EAST: {
            _COMMAND_TYPE: _COMMAND_TYPE_MOVEMENT,
            _COMMAND_DESC_KEY: "Move east",
            _COMMAND_KEY_KEY: "Right",
        },
        Command.MOVE_NORTH: {
            _COMMAND_TYPE: _COMMAND_TYPE_MOVEMENT,
            _COMMAND_DESC_KEY: "Move north",
            _COMMAND_KEY_KEY: "Up",
        },
        Command.MOVE_WEST: {
            _COMMAND_TYPE: _COMMAND_TYPE_MOVEMENT,
            _COMMAND_DESC_KEY: "Move west",
            _COMMAND_KEY_KEY: "Left",
        },
        Command.MOVE_SOUTH: {
            _COMMAND_TYPE: _COMMAND_TYPE_MOVEMENT,
            _COMMAND_DESC_KEY: "Move south",
            _COMMAND_KEY_KEY: "Down",
        },
        # Item commands
        Command.USE_HEALING_POTION: {
            _COMMAND_TYPE: _COMMAND_TYPE_ITEM,
            _COMMAND_DESC_KEY: "Use healing potion",
            _COMMAND_KEY_KEY: "h",
        },
        Command.USE_VISION_POTION: {
            _COMMAND_TYPE: _COMMAND_TYPE_ITEM,
            _COMMAND_DESC_KEY: "Use vision potion",
            _COMMAND_KEY_KEY: "v",
        },
        # Other commands
        Command.SHOW_IN_GAME_MENU: {
            _COMMAND_TYPE: _COMMAND_TYPE_OTHER,
            _COMMAND_DESC_KEY: "Show in-game help menu",
            _COMMAND_KEY_KEY: "Escape",
        },
    }

    def process_keystroke(self, key):
        # Non-movement commands
        if (
            key
            == self.COMMANDS[self.Command.SHOW_IN_GAME_MENU][_COMMAND_KEY_KEY]
        ):
            self._maze_view.show_in_game_menu()
            self._maze_controller.set_active_context("in_game_menu")
        elif (
            key
            == self.COMMANDS[self.Command.USE_HEALING_POTION][_COMMAND_KEY_KEY]
        ):
            self._maze_model.use_item("healing potion")
        elif (
            key
            == self.COMMANDS[self.Command.USE_VISION_POTION][_COMMAND_KEY_KEY]
        ):
            self._maze_model.use_item("vision potion")
        else:
            # Movement commands
            if key == self.COMMANDS[self.Command.MOVE_WEST][_COMMAND_KEY_KEY]:
                self._maze_model.move_adventurer("west")
            elif (
                key == self.COMMANDS[self.Command.MOVE_EAST][_COMMAND_KEY_KEY]
            ):
                self._maze_model.move_adventurer("east")
            elif (
                key == self.COMMANDS[self.Command.MOVE_NORTH][_COMMAND_KEY_KEY]
            ):
                self._maze_model.move_adventurer("north")
            elif (
                key == self.COMMANDS[self.Command.MOVE_SOUTH][_COMMAND_KEY_KEY]
            ):
                self._maze_model.move_adventurer("south")


class QuestionAndAnswerCommandContext(CommandContext):
    # FIXME: Figure out what other keys need to be enabled for a player to
    # answer questions
    class __Command(Enum):
        """Enumeration used to fix commands to a small finite support set."""

        # Item commands
        USE_SUGGESTION_POTION = auto()
        USE_MAGIC_KEY = auto()

    COMMANDS = {
        # Item commands
        __Command.USE_SUGGESTION_POTION: {
            _COMMAND_TYPE: _COMMAND_TYPE_ITEM,
            _COMMAND_DESC_KEY: "Use suggestion potion",
            _COMMAND_KEY_KEY: "s",
        },
        __Command.USE_MAGIC_KEY: {
            _COMMAND_TYPE: _COMMAND_TYPE_ITEM,
            _COMMAND_DESC_KEY: "Use magic key",
            _COMMAND_KEY_KEY: "k",
        },
    }

    def process_keystroke(self, key):
        if (
            key
            == self.COMMANDS[self.__Command.USE_MAGIC_KEY][_COMMAND_KEY_KEY]
        ):
            # FIXME: Display somewhere in the QA pop-up how many magic keys
            # they have left and what button to press to use one
            self._maze_model.use_item("magic key")
        elif (
            key
            == self.COMMANDS[self.__Command.USE_SUGGESTION_POTION][
                _COMMAND_KEY_KEY
            ]
        ):
            # FIXME: Display somewhere in the QA pop-up how many suggestion
            # potions they have left and what button to press to use one
            self._maze_model.use_item("suggestion potion")
        elif key == "Return":
            # FIXME: Get current answer and check if it is correct
            pass
