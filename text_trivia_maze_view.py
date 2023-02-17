import os
from abc import ABC, abstractmethod
import textwrap

from tkinter import *
from tkinter.ttk import *


class TriviaMazeView(ABC):
    """
    A view to display the trivia maze game to the user and gather input
    commands.
    """

    def __init__(self, maze_controller):
        self.__maze_controller = maze_controller

    @abstractmethod
    def show_main_menu(self):
        """Display the main menu"""

    @abstractmethod
    def hide_main_menu(self):
        """Hide the main menu"""

    @abstractmethod
    def show_in_game_menu(self):
        """Show the in-game menu pop-up"""

    @abstractmethod
    def hide_in_game_menu(self):
        """Hide the in-game menu pop-up"""

    @abstractmethod
    def pose_question_and_get_answer(self, question_and_answer):
        """Show the user a question-and-answer pop-up and retrieve the
        answer, then hide the pop-up."""

    @abstractmethod
    def update_map(self):
        """Update the map according to the latest state of the Model."""

    @abstractmethod
    def update_hp_gauge(self):
        """Update the HP gauge to reflect the adventurer's current health
        points."""

    @abstractmethod
    def write_to_event_log(self):
        """Write a message to the event log."""

    @abstractmethod
    def show_game_won_menu(self):
        """Display a pop-up to the user telling them they won the game."""

    @abstractmethod
    def hide_game_won_menu(self):
        """Hide the pop-up to the user telling them they won the game."""

    @abstractmethod
    def show_game_lost_menu(self):
        """Display a pop-up to the user telling them they lost the game."""

    @abstractmethod
    def hide_game_lost_menu(self):
        """Hide the pop-up to the user telling them they lost the game."""


class TextTriviaMazeView:
    """A text-based view for the Trivia Maze application that uses tkinter
    (specifically, themed-tkinter aka "ttk").

    NOTE: Currently, the size is fixed upon creation.
    NOTE: The primary interface (the map, hp gauge, inventory, and event log)
    is technically always shown. The main menu simply consists of overlaying
    the main menu window over the top of the primary interface. Showing the
    primary interface then simply amounts to hiding the main menu (or pop-ups).
    """

    # Primary display config params
    __MAP_WIDTH = 800
    __MAP_HEIGHT = 500
    __SIDEBAR_WIDTH = 250
    __SIDEBAR_HORIZONTAL_PADDING = 15
    __HP_GAUGE_HEIGHT = 30
    __HP_GAUGE_BAR_WIDTH = int(0.8 * __SIDEBAR_WIDTH)
    # __EVENT_LOG_HEIGHT = 50
    __EVENT_LOG_NUM_LINES = 10

    # In-game menu config params
    __IN_GAME_MENU_WIDTH = 400
    __IN_GAME_MENU_TITLE_VERTICAL_PADDING = 5

    # Static messages for menus/popups
    __WELCOME_MESSAGE = """
    _______________________________________________________
    /_______________________________________________________\\
    |               _____    _       _                       |
    |              |_   _|  (_)     (_)                      |
    |                | |_ __ ___   ___  __ _                 |
    |                | | '__| \ \ / / |/ _` |                |
    |                | | |  | |\ V /| | (_| |                |
    |                \_/_|  |_| \_/ |_|\__,_|                |
    |                                                        |
    |                 ___  ___                               |
    |                 |  \/  |                               |
    |                 | .  . | __ _ _______                  |
    |                 | |\/| |/ _` |_  / _ \                 |
    |                 | |  | | (_| |/ /  __/                 |
    |                 \_|  |_/\__,_/___\___|                 |
    |                                                        |
    \________________________________________________________/

         By Daniel S. Karls, Sheehan Smith, Tom J. Swanson
    """
    __YOU_WIN_MESSAGE = """
    _________________________________________________
        __   __                     _         _
        \ \ / /                    (_)       | |
         \ V /___  _   _  __      ___ _ __   | |
          \ // _ \| | | | \ \ /\ / / | '_ \  | |
          | | (_) | |_| |  \ V  V /| | | | | |_|
          \_/\___/ \__,_|   \_/\_/ |_|_| |_| (_)
    _________________________________________________
    """
    __YOU_DIED_MESSAGE = """
     ______     __   __                _ _          _
    /       \   \ \ / /               | (_)        | |
    | @   @ |    \ V /___  _   _    __| |_  ___  __| |
    \   0   /     \ // _ \| | | |  / _` | |/ _ \/ _` |
     |_|_|_|      | | (_) | |_| | | (_| | |  __/ (_| |
                  \_/\___/ \__,_|  \__,_|_|\___|\__,_|
    """

    # Keyboard inputs
    # FIXME: These should all be moved to the controller and accessed by the
    # view through its reference to the controller!
    __KEY_DISMISS_YOU_WIN_OR_GAME_LOST = "Return"

    def __init__(self, title, theme_path=None, theme_name=None):
        # Create primary tkinter window and bind mainloop method (might fit
        # better in the driver and we can just pass the main Tk window into the
        # view init?
        self.__window = Tk()
        self.__window.title(title)
        self.mainloop = self.__window.mainloop

        if theme_path and theme_name:
            # To use this theme, clone the relevant repo and then give the path to its
            # azure.tcl file here
            self.__window.tk.call("source", theme_path)
            self.__window.tk.call("set_theme", theme_name)

        # Set minimum row/col sizes to prevent frames from collapsing to their
        # contained content
        self.__window.rowconfigure(0, minsize=self.__MAP_HEIGHT)
        self.__window.columnconfigure(0, minsize=self.__MAP_WIDTH)
        self.__window.columnconfigure(1, minsize=self.__SIDEBAR_WIDTH)

        # Create primary interface windows
        # NOTE: These windows should be created first. Otherwise, the other
        # widgets will always be "hidden" behind them. You could also get
        # around this by using the 'lift()' and 'lower()' methods of the frame
        # widgets, but it's simpler just to make them in order.
        self.__map = self.__create_map()
        self.__hp_gauge, self.__inventory = self.__add_hp_gauge_and_inventory()
        self.__event_log = self.__create_event_log()

        # Create game won/lost menus
        self.__game_won_menu = self.__create_game_won_menu()
        self.hide_game_won_menu()
        self.__game_lost_menu = self.__create_game_lost_menu()
        self.hide_game_lost_menu()

        # Set up in-game menu
        self.__in_game_menu = self.__create_in_game_menu()
        self.hide_in_game_menu()

        # Create main menu
        self.__main_menu = self.__create_main_menu()
        self.show_main_menu()

        # Prevent resizing
        self.__window.resizable(False, False)

        # Intercept keystrokes from user
        self.__configure_keystroke_capture()

    def __configure_keystroke_capture(self):
        """Capture keystrokes so they can be sent to the controller for
        interpretation"""
        self.__window.bind(
            "<KeyPress>", self.__forward_keystroke_to_controller
        )
        # Also capture arrow keys
        for arrow_key_event in {"<Left>", "<Right>", "<Up>", "<Down>"}:
            self.__window.bind(
                arrow_key_event,
                self.__forward_keystroke_to_controller,
            )

    def __create_main_menu(self):
        options = ("Start game", "Help", "Quit game")
        return MainMenu(self.__window, self.__WELCOME_MESSAGE, options)

    def get_main_menu_current_selection(self):
        return self.__main_menu.selected_option

    def hide_main_menu(self):
        self.__main_menu.hide()

    def show_main_menu(self):
        self.__main_menu.show()

    def __create_in_game_menu(self):
        options = (
            "Back to Game",
            "Display Map Legend",
            "Display Commands",
            "Quit Game",
        )
        return InGameMenu(
            self.__window,
            self.__IN_GAME_MENU_WIDTH,
            "In-Game Menu",
            self.__IN_GAME_MENU_TITLE_VERTICAL_PADDING,
            options,
        )

    def show_in_game_menu(self):
        self.__in_game_menu.show()

    def hide_in_game_menu(self):
        self.__in_game_menu.hide()

    def __create_game_won_menu(self):
        return DismissiblePopUp(
            self.__window,
            None,
            textwrap.dedent(self.__YOU_WIN_MESSAGE),
            5,
            self.__KEY_DISMISS_YOU_WIN_OR_GAME_LOST,
        )

    def show_game_won_menu(self):
        self.__game_won_menu.show()

    def hide_game_won_menu(self):
        self.__game_won_menu.hide()

    def __create_game_lost_menu(self):
        return DismissiblePopUp(
            self.__window,
            None,
            textwrap.dedent(self.__YOU_DIED_MESSAGE),
            5,
            self.__KEY_DISMISS_YOU_WIN_OR_GAME_LOST,
        )

    def show_game_lost_menu(self):
        self.__game_lost_menu.show()

    def hide_game_lost_menu(self):
        self.__game_lost_menu.hide()

    def __forward_keystroke_to_controller(self, event):
        # For regular keys
        key = event.char

        # If char was empty, check to see if it was an arrow key
        if not key or key in os.linesep:
            key = event.keysym

        if key:
            # If keysym wasn't empty, forward it to controller. Otherwise, just
            # ignore it since it's not a supported key command.

            # FIXME: This should really be sent to the controller. Just writing to
            # the event log here for demonstration purposes.
            self.write_to_event_log(f"You pressed {key}")

    def update_hp_gauge(self):
        # FIXME: Retrieve current adventurer HP from Model
        current_hp = 72

        self.__hp_gauge["value"] = current_hp

    def __create_map(self):
        return Map(
            self.__window, self.__MAP_WIDTH, self.__MAP_HEIGHT, 0, 0, 5, ""
        )

    def update_map(self):
        # FIXME: Grab the map object from the model here
        MAP_EXAMPLE = """
        *  *  **  *  **  *  **  *  **  *  **  *  **  *  *
        *  P  ||     ||     ||     ||  I  **@ i  **     *
        *  -  **  *  **  *  **  *  **  -  **  -  **  -  *
        *  -  **  *  **  *  **  *  **  -  **  -  **  -  *
        *  X  ||  V  ||  X  **  V  ||     **     ||     *
        *  *  **  *  **  -  **  -  **  -  **  *  **  -  *
        *  *  **  *  **  -  **  -  **  -  **  *  **  -  *
        *  H  ||  M  **  H  **  O  **     ||  H  **     *
        *  -  **  *  **  -  **  -  **  *  **  *  **  -  *
        *  -  **  *  **  -  **  -  **  *  **  *  **  -  *
        *  A  ||     **     **     **     ||  H  **     *
        *  -  **  -  **  -  **  -  **  -  **  -  **  -  *
        *  -  **  -  **  -  **  -  **  -  **  -  **  -  *
        *     **     ||  H  **     ||     **  H  ||  H  *
        *  *  **  *  **  *  **  *  **  *  **  *  **  *  *
        """
        self.__map.contents = textwrap.dedent(MAP_EXAMPLE)

    def __add_hp_gauge_and_inventory(self):
        side_bar = SideBar(
            window=self.__window,
            width=self.__SIDEBAR_WIDTH,
            height=self.__MAP_HEIGHT,
            row=0,
            column=1,
            rowspan=1,
            columnspan=1,
            padx=0,
            pady=5,
            hp_gauge_height=self.__HP_GAUGE_HEIGHT,
            hp_gauge_bar_width=self.__HP_GAUGE_BAR_WIDTH,
            hp_gauge_label_padx=5,
            hp_gauge_bar_padx=5,
            hp_gauge_bar_pady=15,
            inventory_title_ipady=10,
            inventory_padx=10,
            inventory_pady=8,
        )

        return side_bar.hp_gauge, side_bar.inventory

    def __create_event_log(self):
        return EventLog(
            self.__window, None, self.__EVENT_LOG_NUM_LINES, 1, 0, 1, 2, 3, 5
        )

    def write_to_event_log(self, message):
        self.__event_log.write(message)


class TextMenu:
    """A menu of strings traversable with arrow keys. The selected element can
    be colored differently from the rest of the elements. Intended to be used
    with keystroke detection to make a selection."""

    def __init__(
        self,
        options,
        master,
        width,
        height,
        unselected_foreground_color,
        unselected_background_color,
        selected_foreground_color,
        selected_background_color,
        font,
        justify,
    ):
        self.__options = options
        self.__list_box = Listbox(
            master,
            width=width,
            height=height,
            font=font,
            foreground=unselected_foreground_color,
            background=unselected_background_color,
            selectforeground=selected_foreground_color,
            selectbackground=selected_background_color,
            justify=justify,
        )
        self.__add_options()

        # Pack into containing frame
        self.__list_box.pack()

        # Set first element as selected
        self.__list_box.select_set(0)

    def focus(self):
        """Have this widget take focus"""
        self.__list_box.focus()

    def __add_options(self):
        for ind, option in enumerate(self.__options):
            self.__list_box.insert(ind + 1, option)

    @property
    def selected_option(self):
        return self.__options[self.__list_box.curselection()[0]]

    @selected_option.setter
    def selected_option(self, index):
        self.__list_box.select_set(index)


class SubWindow:
    def __init__(
        self,
        window,
        width,
        height,
        row,
        column,
        rowspan=1,
        columnspan=1,
        relief=RIDGE,  # FIXME: Remove/change default for relief
    ):
        frm = Frame(master=window, width=width, height=height, relief=relief)

        frm.grid(
            row=row,
            column=column,
            rowspan=rowspan,
            columnspan=columnspan,
            sticky="nsew",
        )

        self._frm = frm

    # FIXME: Make show and hide abstract methods? Would the map etc really be a subwindow then?


class MainMenu(SubWindow):
    def __init__(self, window, banner_text, menu_options):
        """Create a frame inside of `window` that fills up its entire row and
        column span"""
        super().__init__(window, None, None, 0, 0, *window.grid_size())

        # Add banner message
        # TODO: Store all styles in a single place (possibly some kind of view
        # configuration class)
        style_name = "welcome.TLabel"
        sty = Style()

        sty.configure(style_name, font=("Courier New", 16))

        lbl = Label(
            master=self._frm,
            text=banner_text,
            justify=CENTER,
            anchor=CENTER,
            style=style_name,
        )

        lbl.pack(fill=BOTH)

        # Add text menu with desired options
        self.__text_menu = TextMenu(
            options=menu_options,
            master=self._frm,
            width=None,
            height=len(menu_options),
            unselected_foreground_color="grey",
            unselected_background_color="black",
            selected_foreground_color="black",
            selected_background_color="white",
            font=("Courier New", 18),
            justify=CENTER,
        )

    def hide(self):
        self._frm.grid_remove()

    def show(self):
        self._frm.grid()

        # Attach focus to text menu of options
        self.__text_menu.focus()
        self.__text_menu.selected_option = 0

    @property
    def selected_option(self):
        return self.__text_menu.selected_option

    @selected_option.setter
    def selected_option(self, index):
        self.__text_menu.selected_option = index


class Map(SubWindow):
    def __init__(self, window, width, height, row, column, padx, text):
        super().__init__(
            window,
            width,
            height,
            row,
            column,
        )
        self.__text = text

        # Create empty label that will hold the actual map
        style_name = "map.TLabel"
        sty = Style()
        sty.configure(style_name, font=("Courier New", 26, "bold"))
        lbl = Label(
            master=self._frm,
            text=text,
            style=style_name,
            justify=CENTER,
            anchor=CENTER,
        )
        lbl.pack(padx=padx, fill=BOTH)

    @property
    def contents(self):
        return self.__text

    @contents.setter
    def contents(self, text):
        self._frm.children["!label"].configure(text=text)


class EventLog(SubWindow):
    def __init__(
        self,
        window,
        width,
        num_lines,
        row,
        column,
        rowspan,
        columnspan,
        padx,
        pady,
    ):
        super().__init__(window, width, None, row, column, rowspan, columnspan)

        self.__textbox = self.__add_scrollable_readonly_textbox_to_subwindow(
            self._frm, num_lines, padx, pady
        )

    def write(self, message):
        event_log_text_box = self.__textbox

        # Make text box writable for a brief instant, write to it, then make it
        # read-only again
        event_log_text_box.config(state=NORMAL)
        event_log_text_box.insert(END, message + "\n")
        event_log_text_box.config(state=DISABLED)

        # Scroll down as far as possible
        event_log_text_box.yview(END)

    @staticmethod
    def __add_scrollable_readonly_textbox_to_subwindow(
        subwindow, num_lines, padx, pady
    ):
        frm = subwindow
        scrlbar = Scrollbar(master=frm, orient=VERTICAL)
        scrlbar.pack(side=RIGHT, pady=pady, fill=Y, padx=padx)

        scrltxt = Text(
            master=frm,
            height=num_lines,
            yscrollcommand=scrlbar.set,
        )
        scrltxt.pack(fill=BOTH, pady=pady)

        # Enable dragging of scroll bar now that text box exists (has to be
        # done in this order)
        scrlbar.config(command=scrltxt.yview)

        # Make text box read-only
        scrltxt.config(state=DISABLED)

        return scrltxt


class PopUpWindow:
    # FIXME: Remove/change default for relief
    def __init__(self, window, width, relief=RIDGE):
        self._frm = Frame(
            master=window,
            relief=relief,
        )
        self._place_pop_up_at_center_of_window(self._frm, width)
        self._width = width

    @staticmethod
    def _place_pop_up_at_center_of_window(frame, width):
        frame.place(
            relx=0.5,
            rely=0.5,
            anchor=CENTER,
            width=width,
        )

    # FIXME: Make show and hide abstract methods? Would the map etc really be a subwindow then?


class SideBar(SubWindow):
    def __init__(
        self,
        window,
        width,
        height,
        row,
        column,
        rowspan,
        columnspan,
        padx,
        pady,
        hp_gauge_height,
        hp_gauge_bar_width,
        hp_gauge_label_padx,
        hp_gauge_bar_padx,
        hp_gauge_bar_pady,
        inventory_title_ipady,
        inventory_padx,
        inventory_pady,
    ):
        super().__init__(
            window, width, height, row, column, rowspan, columnspan
        )
        # Create frame to hold hp gauge label and bar
        frm_hp = Frame(master=self._frm, height=hp_gauge_height)
        frm_hp.pack(
            side=TOP,
            padx=padx,
            pady=pady,
        )

        # Create label for hp gauge
        style_name = "inventory_title.TLabel"
        sty = Style()
        sty.configure(style_name, font=("Arial", 16, "bold"))
        lbl_hp_gauge = Label(master=frm_hp, text="HP", style=style_name)
        lbl_hp_gauge.pack(padx=(hp_gauge_label_padx, 0), side=LEFT)

        # Create bar for hp gauge
        bar_hp_gauge = Progressbar(
            master=frm_hp,
            orient=HORIZONTAL,
            length=hp_gauge_bar_width,
            mode="determinate",
        )
        bar_hp_gauge.pack(padx=hp_gauge_bar_padx, pady=hp_gauge_bar_pady)
        bar_hp_gauge["value"] = 100
        self.hp_gauge = bar_hp_gauge

        # Create label for inventory
        style_name = "inventory_title.TLabel"
        sty = Style()
        sty.configure(style_name, font=("Arial", 16, "bold"))
        lbl_inventory = Label(
            master=self._frm,
            text="Inventory",
            relief=RIDGE,
            anchor=CENTER,
            style=style_name,
        )
        lbl_inventory.pack(
            side=TOP,
            ipady=inventory_title_ipady,
            fill=BOTH,
        )

        self.inventory = self.__create_inventory_item_labels(
            self._frm, inventory_padx, inventory_pady
        )

    @staticmethod
    def __create_inventory_item_labels(frm, padx, pady):
        # Create inventory_labels
        item_labels = (
            "Health Potion",
            "Suggestion Potion",
            "Vision Potion",
            "Magic Key",
            "Pillar of Abstraction",
            "Pillar of Encapsulation",
            "Pillar of Inheritance",
            "Pillar of Polymorphism",
        )
        inventory_quantity_labels = {}
        style_name = "inventory_item.TLabel"
        sty = Style()
        sty.configure(style_name, font=("Arial", 15, "bold"))
        for item in item_labels:
            # Create frame for this item
            frm_item = Frame(master=frm)
            frm_item.pack(side=TOP, fill=BOTH, padx=padx, pady=pady)

            # Create label for item
            lbl_item = Label(master=frm_item, text=item, style=style_name)
            lbl_item.pack(side=LEFT, padx=padx)

            # Create label holding quantity of item
            lbl_quantity = Label(master=frm_item, text="0", style=style_name)
            lbl_quantity.pack(side=RIGHT, padx=padx)

            inventory_quantity_labels[item] = lbl_quantity

        return inventory_quantity_labels


class InGameMenu(PopUpWindow):
    """
    A pop-up window with a text-based menu inside.
    """

    # FIXME: Remove/change default for relief
    def __init__(self, window, width, title, pady, menu_options, relief=RIDGE):
        # Create the frame for the whole in-game menu
        super().__init__(window, width, relief)

        # Create header with title in it
        frm_title = Frame(master=self._frm, width=width, relief=relief)
        frm_title.pack(fill=BOTH, anchor=CENTER)
        lbl = Label(
            master=frm_title,
            text=title,
            justify=CENTER,
            anchor=CENTER,
        )
        lbl.pack(fill=BOTH, pady=pady)

        self.__text_menu = TextMenu(
            options=menu_options,
            master=self._frm,
            width=width,
            height=len(menu_options),
            unselected_foreground_color="grey",
            unselected_background_color="black",
            selected_foreground_color="black",
            selected_background_color="white",
            font=("Courier New", 18),
            justify=CENTER,
        )

    def show(self):
        self._place_pop_up_at_center_of_window(self._frm, self._width)
        self.__text_menu.focus()
        self.__text_menu.selected_option = 0

    def hide(self):
        self._frm.place_forget()

    @property
    def selected_option(self):
        return self.__text_menu.selected_option

    @selected_option.setter
    def selected_option(self, index):
        self.__text_menu.selected_option = index


class DismissiblePopUp(PopUpWindow):
    """
    A pop-up window that simply displays a message and allows the user to
    dismiss it by entering a specific key.
    """

    def __init__(self, window, width, text, pady, dismiss_key, relief=RIDGE):
        # Create the frame for the whole in-game menu
        super().__init__(window, width, relief)

        # TODO: Store all styles in a single place (possibly some kind of view
        # configuration class)
        style_name = "you_won.TLabel"
        sty = Style()
        sty.configure(style_name, font=("Courier New", 16))

        lbl = Label(
            master=self._frm,
            text=text,
            justify=CENTER,
            anchor=CENTER,
            style=style_name,
        )
        lbl.pack(fill=BOTH, pady=pady)

        # Put return to main menu option below
        lbl = Label(
            master=self._frm,
            text=f"Press [{dismiss_key}] to return to main menu",
            justify=CENTER,
            anchor=CENTER,
        )
        lbl.pack(
            fill=BOTH,
        )

    def show(self):
        self._place_pop_up_at_center_of_window(self._frm, self._width)

    def hide(self):
        self._frm.place_forget()


if __name__ == "__main__":
    view = TextTriviaMazeView("TriviaMaze")

    view.hide_main_menu()
    view.update_map()
    view.show_game_lost_menu()
    view.hide_game_lost_menu()
    for i in range(100):
        view.write_to_event_log(f"Here is message {i}")
    view.mainloop()
