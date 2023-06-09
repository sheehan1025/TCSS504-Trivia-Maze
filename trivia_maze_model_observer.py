from abc import ABC, abstractmethod
from trivia_maze import TriviaMaze


class TriviaMazeModelObserver(ABC):
    def __init__(self, trivia_maze: TriviaMaze):
        """Bind given TriviaMaze to instance attr and register as an observer
        with it.
        """
        self._maze_model = trivia_maze
        self._maze_model.register_observer(self)

    @abstractmethod
    def update(self):
        """Perform any necessary updates to self whenever the maze model emits
        a notification."""
