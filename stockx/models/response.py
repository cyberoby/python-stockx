from dataclasses import dataclass, field
from typing import Any

from ..format import pretty_str
from ..types_ import JSON


@pretty_str
@dataclass(frozen=True, slots=True)
class Response:
    """API response.

    Parameters
    ----------
    status_code : `int`
    message : `str`
    data : `JSON`
    """
    status_code: int
    message: str = ''
    data: JSON = field(default_factory=list)