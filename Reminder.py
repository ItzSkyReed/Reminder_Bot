from io import BytesIO
from typing import Literal

from pendulum import Timezone

from ReminderTime import ReminderTime


class Reminder:
    def __init__(self, user_id: int, channel_id: int, time: str, name: str, description: str | None,
                 rem_type: Literal['Daily','Date'], timezone: Timezone, link: str = None, file: bytes | None = None,
                 file_name: str = None, private: bool = False, mention_role: int | None = None):

        self._user_id = user_id
        self._channel_id = channel_id
        self._name = name
        self._description = description
        self._rem_type = rem_type
        self._file = file
        self._private = private
        self._timezone = timezone
        self._file_name = file_name
        self._link = link
        self._mention_role = mention_role

        self._time = ReminderTime(time, self._timezone, self._rem_type)

    @property
    def link(self):
        return self._link

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def rem_time(self) -> ReminderTime:
        return self._time

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def rem_type(self) -> str:
        return self._rem_type

    @property
    def file(self) -> BytesIO | None:
        return self._file

    @property
    def timezone(self) -> Timezone:
        return self._timezone

    @property
    def file_name(self) -> str | None:
        return self._file_name

    @property
    def private(self) -> bool:
        return self._private

    @property
    def mention_role(self) -> int | None:
        return self._mention_role