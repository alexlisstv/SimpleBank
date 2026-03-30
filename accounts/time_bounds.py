"""Parse optional `from` / `to` query parameters for transaction time filtering (UTC-aware)."""

from datetime import datetime, time, timezone as dt_timezone

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.exceptions import ValidationError


def _flatten_validation_messages(detail) -> list[str]:
    if isinstance(detail, list):
        return [str(item) for item in detail]
    if isinstance(detail, dict):
        out: list[str] = []
        for v in detail.values():
            out.extend(_flatten_validation_messages(v))
        return out
    return [str(detail)]


def _parse_one(value: str, *, end_of_calendar_day: bool) -> datetime:
    value = value.strip()
    if not value:
        raise ValidationError("Empty value.")
    # Prefer calendar dates first so `YYYY-MM-DD` is not treated as midnight-only via parse_datetime.
    d = parse_date(value)
    if d is not None:
        t = time.max if end_of_calendar_day else time.min
        naive = datetime.combine(d, t)
        return timezone.make_aware(naive, dt_timezone.utc)
    dt = parse_datetime(value)
    if dt is not None:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, dt_timezone.utc)
        return dt
    raise ValidationError("Expected ISO 8601 date (YYYY-MM-DD) or datetime.")


def transaction_time_bounds(query_params) -> tuple[datetime | None, datetime | None]:
    """
    Returns (start inclusive, end inclusive) for filtering `timestamp`.
    Date-only `to` includes the whole calendar day in UTC.
    """
    errors: dict[str, list[str]] = {}
    start: datetime | None = None
    end: datetime | None = None

    raw_from = query_params.get("from")
    if raw_from not in (None, ""):
        try:
            start = _parse_one(str(raw_from), end_of_calendar_day=False)
        except ValidationError as exc:
            errors.setdefault("from", []).extend(_flatten_validation_messages(exc.detail))

    raw_to = query_params.get("to")
    if raw_to not in (None, ""):
        try:
            end = _parse_one(str(raw_to), end_of_calendar_day=True)
        except ValidationError as exc:
            errors.setdefault("to", []).extend(_flatten_validation_messages(exc.detail))

    if errors:
        raise ValidationError(errors)

    if start is not None and end is not None and start > end:
        raise ValidationError("'from' must be earlier than or equal to 'to'.")

    return start, end
