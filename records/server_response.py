from dataclasses import dataclass

from records.records_helper import BetterDataclass
@dataclass
class ServerResponse(BetterDataclass):
    success: bool = False
    error: str = ""
    data: str = ""
    debug: str = ""
    extra: str = ""

    def reset(self) -> None:
        self.success = False
        self.error = ""
        self.data = ""
        self.debug = ""
        self.extra = ""