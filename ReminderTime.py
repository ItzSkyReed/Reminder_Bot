import re

from pendulum import Timezone, DateTime, now

from constants import HH_MM_pattern, FULL_DATE_pattern, TIMER_TIME_patterns


class TimeException(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class TimeInPastException(TimeException):
    def __init__(self, message: str = None):
        super().__init__(message)


class ExcessiveFutureTimeException(TimeException):
    def __init__(self, message: str = None):
        super().__init__(message)


class InvalidTimeFormatException(TimeException):
    def __init__(self, message: str = None):
        super().__init__(message)


class InvalidReminderTypeException(TimeException):
    def __init__(self, message: str = None):
        super().__init__(message)


class ReminderTime:
    _time_units = {
        'д': 'days',
        'd': 'days',
        'ч': 'hours',
        'h': 'hours',
        'м': 'minutes',
        'm': 'minutes',
    }

    def __init__(self, unformatted_time: str, timezone: Timezone, rem_type: str, minimal_minutes_from_now: int = 1):
        self._reminder_type = rem_type
        self._minimal_minutes_from_now = minimal_minutes_from_now
        time = self._parse_time(unformatted_time, timezone)
        self._time = time

    def _parse_time(self, time: str, timezone: Timezone):
        if re.fullmatch(HH_MM_pattern, time):
            return self._parse_hh_mm_pattern(time, timezone)

        if any(re.search(pattern, time) for pattern in TIMER_TIME_patterns.values()):
            return self._parse_timer_format(time, timezone)

        if self._reminder_type == 'Daily':
            raise InvalidReminderTypeException('\"Daily\" type of reminder can not be used with full date pattern')

        if full_date_match := re.fullmatch(FULL_DATE_pattern, time):
            return self._parse_full_date_pattern(full_date_match, timezone)

        raise InvalidTimeFormatException('Invalid time format')

    @staticmethod
    def _parse_hh_mm_pattern(time_str: str, timezone: Timezone) -> DateTime:
        hours, minutes = map(int, time_str.split(':'))
        now_utc = now("UTC")
        this_day = now_utc.in_tz(timezone).set(hour=hours, minute=minutes, second=0, microsecond=0).in_tz("UTC")

        if this_day >= now_utc.add(minutes=1):
            return this_day
        return this_day.add(days=1)

    def _parse_full_date_pattern(self, time_match: re.Match, timezone: Timezone) -> DateTime:
        day, month, year, hours, minutes = time_match.groups()

        if not year:
            year = str(now(tz=timezone).year)

        day, month, year, hours, minutes = map(int, [day, month, year, hours, minutes])

        time = DateTime.create(year, month, day, hours, minutes, tz=timezone).in_tz("UTC")

        self._validate(time)

        return time

    def _parse_timer_format(self, time_str: str, timezone: Timezone) -> DateTime | None:
        weeks = 0
        days = 0
        hours = 0
        minutes = 0
        seconds = 0

        for key, pattern in TIMER_TIME_patterns.items():
            matches = re.findall(pattern, time_str)
            if matches:
                total = sum(map(int, matches))
                if key == 'weeks':
                    weeks += total
                elif key == 'days':
                    days += total
                elif key == 'hours':
                    hours += total
                elif key == 'minutes':
                    minutes += total
                elif key == 'seconds':
                    seconds += total    

        days = weeks * 7 + days
        try:
            time = now('UTC').in_tz(timezone).add(days=days, hours=hours, minutes=minutes, seconds=seconds).in_tz("UTC")
        except OverflowError:
            raise ExcessiveFutureTimeException()

        self._validate(time)

        return time

    def _validate(self, time: DateTime) -> None:
        now_utc = now("UTC")
        if time > now_utc.add(years=2):
            raise ExcessiveFutureTimeException()

        if time <= now_utc.add(minutes=self._minimal_minutes_from_now):
            raise TimeInPastException()

    @property
    def time(self) -> DateTime:
        return self._time

    @property
    def bd_timestamp(self) -> int:
        if self._reminder_type == 'Date':
            return int(self._time.timestamp())

        else:
            return self._time.hour * 3600 + self._time.minute * 60 + self._time.second

    def __repr__(self):
        return f"{self.__class__.__name__}({self.time} UTC)"
