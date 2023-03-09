from enum import Enum


class ConnectionStatus(Enum):
    PENDING = 0
    ESTABLISHED = 1
    CLOSED = 2


class Connection():
    def __init__(self) -> None:
        self.status = ConnectionStatus.PENDING
