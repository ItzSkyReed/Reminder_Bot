import asyncio
from typing import Self, Sequence, Literal

import pendulum
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, BLOB, select, Index, insert, update, Boolean, delete, func, and_

from ReminderTime import ReminderTime
from constants import UTC_ZONES, DISPATCHER_PERIOD, DATABASE_NAME

DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_NAME}"
engine = create_async_engine(DATABASE_URL, echo=False)

Base = declarative_base()
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False)


def connection(method):
    async def wrapper(*args, **kwargs):
        async with AsyncSessionMaker() as session:
            try:
                return await method(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    return wrapper


class UserDB(Base):
    __tablename__ = "Users"

    # Используем discord_id как primary key
    discord_id = Column(Integer, unique=True, primary_key=True, nullable=False, autoincrement=False)
    timezone = Column(Integer, ForeignKey("Timezone.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=False, default=1)

    tz_relation = relationship("TimezoneDB", backref="users")

    @classmethod
    @connection
    async def create_user_if_not_exists(cls, discord_id: int, session: AsyncSession):
        stmt = insert(cls).values(discord_id=discord_id).prefix_with("OR IGNORE")
        await session.execute(stmt)
        await session.commit()

    @classmethod
    @connection
    async def get_user_timezone(cls, discord_id: int, session: AsyncSession) -> "TimezoneBD | None":
        result = await session.execute(
            select(TimezoneDB).join(cls, cls.timezone == TimezoneDB.id).filter(cls.discord_id == discord_id)
        )
        return result.scalars().first()

    @classmethod
    @connection
    async def update_user_timezone(cls, discord_id: int, new_timezone: str, session: AsyncSession) -> None:
        subquery = select(TimezoneDB.id).filter(TimezoneDB.tz_name == new_timezone).scalar_subquery()
        await session.execute(
            update(cls)
            .where(cls.discord_id == discord_id)
            .values(timezone=subquery)
        )
        await session.commit()


class TimezoneDB(Base):
    __tablename__ = "Timezone"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    tz_name = Column(String, unique=True, nullable=False)

    @classmethod
    @connection
    async def insert_timezones(cls, session: AsyncSession):
        stmt = select(cls).limit(1)
        result = await session.execute(stmt)
        existing_timezone = result.scalar()
        if existing_timezone:
            return
        timezones = [cls(tz_name=name) for name in UTC_ZONES.keys()]
        session.add_all(timezones)
        await session.commit()


class RemindersDB(Base):
    __tablename__ = "Reminders"

    id = Column(Integer, primary_key=True, unique=True, nullable=False, autoincrement=True)
    # Внешний ключ ссылается на Users.discord_id
    user_id = Column(Integer, ForeignKey("Users.discord_id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    name = Column(String, nullable=False)
    channel_id = Column(Integer, nullable=False)
    timestamp = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String)
    file = Column(BLOB)
    file_name = Column(String)
    private = Column(Boolean, nullable=False, default=False)
    link = Column(String)
    mention_role = Column(Integer)

    user = relationship("UserDB", backref="reminders")

    __table_args__ = (Index('ix_reminders_timestamp_type', 'timestamp', 'type'),)

    @connection
    async def delete(self, session: AsyncSession):
        await session.delete(self)
        await session.commit()

    @connection
    async def remove_file(self, session: AsyncSession):
        self.file = None
        self.file_name = None
        await session.commit()

    @connection
    async def save(self, session: AsyncSession):
        if self.id:
            await session.merge(self)
        else:
            session.add(self)
        await session.commit()

    @classmethod
    @connection
    async def add_reminder(cls, user_id: int, channel_id: int, time: ReminderTime, name: str, description: str | None,
                           rem_type: Literal['Daily', 'Date'], link: str, file: bytes | None,
                           file_name: str, private: bool, mention_role: int | None, session: AsyncSession):
        """
        Adds a new reminder to the database.

        Args:
            user_id (int): The ID of the user creating the reminder.
            channel_id (int): The ID of the channel where the reminder will be sent.
            time (ReminderTime): The time at which the reminder will trigger.
            name (str): The name of the reminder.
            description (str | None): The description of the reminder.
            rem_type (Literal['Daily', 'Date']): The type of the reminder, either 'Daily' or 'Date'.
            link (str): A link associated with the reminder.
            file (bytes | None): An optional file to be sent with the reminder.
            file_name (str): The name of the file to be sent.
            private (bool): Whether the reminder is private.
            mention_role (int | None): The role to mention when the reminder is sent.
            session (AsyncSession): The database session to use for the operation.

        Returns:
            None
        """
        user_subquery = select(UserDB.discord_id).where(UserDB.discord_id == user_id).scalar_subquery()
        insert_stmt = insert(cls).values(
            user_id=user_subquery,
            name=name,
            channel_id=channel_id,
            timestamp=time.bd_timestamp,
            type=rem_type,
            description=description,
            file=file,
            file_name=file_name,
            private=private,
            link=link,
            mention_role=mention_role
        )
        await session.execute(insert_stmt)
        await session.commit()

    @classmethod
    @connection
    async def get_due_and_delete_date(cls, session: AsyncSession) -> Sequence[Self]:
        current_timestamp = int(pendulum.now("UTC").timestamp())

        delete_query = (
            delete(cls)
            .where(cls.timestamp <= current_timestamp, cls.type == "Date")
            .returning(cls)
        )
        result = await session.execute(delete_query)
        await session.commit()

        return result.scalars().all()

    @classmethod
    @connection
    async def get_due_daily(cls, session: AsyncSession) -> Sequence[Self]:
        current_time = pendulum.now("UTC")
        today_time = current_time.hour * 3600 + current_time.minute * 60 + current_time.second

        reminders_query = select(cls).where(
            and_(
                cls.timestamp >= today_time,
                cls.timestamp < today_time + DISPATCHER_PERIOD,
                cls.type == "Daily"
            )
        )
        result = await session.execute(reminders_query)
        reminders_to_send = result.scalars().all()

        return reminders_to_send

    @classmethod
    @connection
    async def get_user_reminders_count(cls, discord_id: int, session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count(cls.user_id)).where(cls.user_id == discord_id)
        )
        return result.scalar()

    @classmethod
    @connection
    async def get_reminder_by_id(cls, rem_id: int, session: AsyncSession):
        result = await session.execute(
            select(cls).where(cls.id == rem_id)
        )
        return result.scalar()

    @classmethod
    @connection
    async def get_user_reminders_without_file(cls, discord_id: int, session: AsyncSession):
        result = await session.execute(
            select(
                cls.id, cls.user_id, cls.name, cls.channel_id, cls.timestamp,
                cls.type, cls.description, cls.file_name, cls.private, cls.link, cls.mention_role
            ).where(cls.user_id == discord_id)
        )

        reminders = []
        for row in result.all():
            reminders.append(
                cls(
                    id=row.id,
                    user_id=row.user_id,
                    name=row.name,
                    channel_id=row.channel_id,
                    timestamp=row.timestamp,
                    type=row.type,
                    description=row.description,
                    file_name=row.file_name,
                    private=row.private,
                    link=row.link,
                    mention_role=row.mention_role,
                    file=None
                )
            )
        return reminders


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Insert time zones if they are not yet in the database
        await TimezoneDB.insert_timezones()


asyncio.run(init_db())
