from dataclasses import dataclass, field

@dataclass
class Response:
    status_code: int
    message: str = ''
    data: dict | list[dict] = field(default_factory=list)

