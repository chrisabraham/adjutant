"""Local time. Every "today", "overdue" and "this week" goes through here.

ADJUTANT_NOW pins the clock (tests, replays). ADJUTANT_TIMEZONE picks the zone.
"""

import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def zone():
    return ZoneInfo(os.environ.get("ADJUTANT_TIMEZONE", "America/New_York"))


def current():
    pinned = os.environ.get("ADJUTANT_NOW")
    if pinned:
        moment = datetime.fromisoformat(pinned)
        return moment if moment.tzinfo else moment.replace(tzinfo=zone())
    return datetime.now(zone())


def now():
    """An ISO timestamp for the record."""
    return current().isoformat(timespec="seconds")


def today():
    return current().date()


def describe_day(iso_day):
    """'2026-10-26' -> 'Mon Oct 26', 'today' or 'tomorrow'."""
    day = date.fromisoformat(iso_day[:10])
    if day == today():
        return "today"
    if day == today() + timedelta(days=1):
        return "tomorrow"
    return day.strftime("%a %b %-d")


def utc_range(days_back):
    """(since, until) in Todoist's UTC format, covering the last `days_back` local days through now."""
    start = datetime.combine(today() - timedelta(days=days_back), datetime.min.time(), zone())
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return (start.astimezone(ZoneInfo("UTC")).strftime(fmt),
            current().astimezone(ZoneInfo("UTC")).strftime(fmt))
