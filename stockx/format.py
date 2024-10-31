from collections.abc import Iterable
from datetime import datetime


def iso(datetime: datetime | None) -> str | None:
    if not datetime:
        return None
    return f'{datetime.isoformat(timespec='seconds')}Z'


def comma_separated(values: Iterable[str] | None) -> str | None:
    return ','.join(values) if values else None


def iso_date(datetime: datetime | None) -> str | None:
    return datetime.strftime('%Y-%m-%d') if datetime else None