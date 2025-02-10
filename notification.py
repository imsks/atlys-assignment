from abc import ABC, abstractmethod
import logging

class BaseNotification(ABC):
    @abstractmethod
    def send(self, message: str):
        pass


class ConsoleNotification(BaseNotification):
    """
    Concrete strategy for console-based notification.
    """
    def send(self, message: str):
        print(message)
        # or use logging
        logging.info(message)