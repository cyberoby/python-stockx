from dataclasses import dataclass, field
from typing import Any

from ..format import pretty_str


@pretty_str
@dataclass(frozen=True, slots=True)
class Response: 
    status_code: int
    message: str = '', 
    data: dict[str, Any] | list[dict[str, Any]] = field(default_factory=list)