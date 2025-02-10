from abc import ABC, abstractmethod
import logging

class BaseNotification(ABC):
    @abstractmethod
    def send(self, message: str):
        pass

class ConsoleNotification(BaseNotification):
    def send(self, message: str):
        logging.info(message)