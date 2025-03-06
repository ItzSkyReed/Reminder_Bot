import io
from typing import Literal

import discord
from discord import Embed
from discord.ui import Modal, InputText, View
from pendulum import Timezone

import Database
from ReminderTime import ReminderTime, TimeInPastException, ExcessiveFutureTimeException, InvalidReminderTypeException, InvalidTimeFormatException
from constants import REMINDER_MESSAGE_COLOR, FILE_ICON, EMBED_IMAGE_TYPES, ERROR_MESSAGE_COLOR, UTC_ZONES


class EditErrorEmbed(Embed):
    def __init__(self, message: str, error: str = "Input error"):
        super().__init__()
        self.color = ERROR_MESSAGE_COLOR
        self.title = error
        self.description = message


class ReminderEditEmbed(Embed):
    def __init__(self, reminder: Database.RemindersBD, embed_type: Literal["short", "full"], **kwargs):
        super().__init__(**kwargs)
        self._reminder_id = reminder.id
        self.title = f"Reminder: {reminder.name}"
        self.color = REMINDER_MESSAGE_COLOR

        if reminder.description is not None:
            if embed_type == "short" and len(reminder.description) > 140:
                description = reminder.description[:150] + "..."
            else:
                description = reminder.description
        else:
            description = "*Not Provided*"
        self.add_field(name="📝 Description", value=description or 'Not provided', inline=False)

        self.add_field(name="🔖 Type", value=f"`{reminder.type}`")
        self.add_field(name="🔒 Privacy", value='`Private`' if reminder.private else '`Public`')
        date = f"<t:{reminder.timestamp}:f>" if reminder.type == "Date" else f"<t:{reminder.timestamp}:t>"
        self.add_field(name="📅 Date", value=date)

        if reminder.link:
            link = reminder.link if len(reminder.link) < 30 else reminder.link.split("https://", maxsplit=1)[-1][:27] + "..."
            self.add_field(name="🔗 Link:", value=f"[{link}]({reminder.link})")

        if reminder.file_name is not None:
            if embed_type == "short":
                self.set_footer(text=f"File: {reminder.file_name}", icon_url=FILE_ICON)
            else:
                if reminder.file_name.split(".")[-1].lower() in EMBED_IMAGE_TYPES:
                    self.set_image(url=f"attachment://{reminder.file_name}")

    @property
    def reminder_id(self):
        return self._reminder_id


class EditNameModal(Modal):
    def __init__(self, reminder: Database.RemindersBD):
        super().__init__(title="Edit Reminder Name", timeout=180)
        self.add_item(InputText(label="New Name", placeholder="Enter new reminder name", max_length=100, min_length=3))
        self.reminder = reminder

    async def callback(self, interaction: discord.Interaction):
        if self.children[0].value == self.reminder.name:
            return await interaction.response.send_message(embed=EditErrorEmbed(message="The new name is the same as the previous one"), ephemeral=True)

        self.reminder.name = self.children[0].value
        await self.reminder.save()
        new_embed = ReminderEditEmbed(reminder=self.reminder, embed_type="full")

        return await interaction.response.edit_message(embed=new_embed)


class EditDescriptionModal(Modal):
    def __init__(self, reminder: Database.RemindersBD):
        super().__init__(title="Edit Reminder Description", timeout=300)
        self.add_item(InputText(label="New description", placeholder="Enter new reminder description", max_length=1000, style=discord.InputTextStyle.multiline, required=False))
        self.reminder = reminder

    async def callback(self, interaction: discord.Interaction):
        if self.children[0].value == self.reminder.description:
            return await interaction.response.send_message(embed=EditErrorEmbed(message="The new description is the same as the previous one"), ephemeral=True)

        self.reminder.description = self.children[0].value
        await self.reminder.save()
        new_embed = ReminderEditEmbed(reminder=self.reminder, embed_type="full")

        return await interaction.response.edit_message(embed=new_embed)


class EditLinkModal(Modal):
    def __init__(self, reminder: Database.RemindersBD):
        super().__init__(title="Edit Reminder link", timeout=180)
        self.add_item(InputText(label="New link", placeholder="Enter new reminder link", max_length=1000, style=discord.InputTextStyle.multiline, required=False))
        self.reminder = reminder

    async def callback(self, interaction: discord.Interaction):
        if self.children[0].value == self.reminder.description:
            return await interaction.response.send_message(embed=EditErrorEmbed(message="The new link is the same as the previous one"), ephemeral=True)
        if self.children[0].value and not self.children[0].value.startswith("https://"):
            return await interaction.response.send_message(embed=EditErrorEmbed(message="The link should start with \"https://\""), ephemeral=True)

        self.reminder.link = self.children[0].value
        await self.reminder.save()
        new_embed = ReminderEditEmbed(reminder=self.reminder, embed_type="full")

        return await interaction.response.edit_message(embed=new_embed)


class EditTimeModal(Modal):
    def __init__(self, reminder: Database.RemindersBD):
        super().__init__(title="Edit Reminder Time", timeout=300)
        self.reminder = reminder
        self.add_item(InputText(label="New time", placeholder="Enter new reminder time", max_length=100, min_length=2))
        self.add_item(InputText(label="New type: Daily/Date", placeholder=f"Current type: {self.reminder.type}",
                                max_length=5, min_length=4, value=self.reminder.type, required=False))

    async def callback(self, interaction: discord.Interaction):
        if self.children[1].value is None:
            new_type = self.reminder.type
        elif (temp_new_type := self.children[1].value.lower().capitalize()) not in {"Daily", "Date"}:
            return await interaction.response.send_message(
                embed=EditErrorEmbed(message=f"Reminder type: {temp_new_type} is incorrect, possible types: \"Daily\", \"Date\""), ephemeral=True)
        else:
            new_type = temp_new_type
        tz = await Database.UserBD.get_user_timezone(self.reminder.user_id)
        try:
            time = ReminderTime(self.children[0].value, rem_type=new_type, timezone=Timezone(UTC_ZONES[tz.tz_name]), minimal_minutes_from_now=10)

        except TimeInPastException:
            return await interaction.response.send_message(embed=EditErrorEmbed("The specified time is in the past, or too close to the present."), ephemeral=True)

        except ExcessiveFutureTimeException:
            return await interaction.response.send_message(embed=EditErrorEmbed("The maximum reminder duration is 2 years."), ephemeral=True)

        except InvalidReminderTypeException:
            return await interaction.response.send_message(embed=EditErrorEmbed("\"Daily\" reminder type can be used only with HH:MM time format"), ephemeral=True)

        except InvalidTimeFormatException:
            return await interaction.response.send_message(embed=EditErrorEmbed("The specified time format cannot be parsed"), ephemeral=True)

        if self.reminder.timestamp == time.bd_timestamp:
            return await interaction.response.send_message(embed=EditErrorEmbed(message="The new time is the same as the previous one"), ephemeral=True)

        self.reminder.timestamp = time.bd_timestamp
        self.reminder.type = new_type
        await self.reminder.save()
        new_embed = ReminderEditEmbed(reminder=self.reminder, embed_type="full")

        return await interaction.response.edit_message(content="### Choose Field to Edit", embed=new_embed)


class ReminderEditView(View):
    def __init__(self, reminder: Database.RemindersBD):
        super().__init__(disable_on_timeout=True)
        self.reminder = reminder

        if not self.reminder.file_name:
            self.remove_item(self.get_remove_file_button())

    def get_remove_file_button(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "Remove File":
                return child
        return None

    @discord.ui.button(label="Edit Name", style=discord.ButtonStyle.primary, emoji="✏️", row=0)
    async def edit_name_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = EditNameModal(reminder=self.reminder)
        await interaction.response.send_modal(modal=modal)

    @discord.ui.button(label="Edit Description", style=discord.ButtonStyle.primary, emoji="📝", row=0)
    async def edit_desc_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = EditDescriptionModal(reminder=self.reminder)
        await interaction.response.send_modal(modal=modal)

    @discord.ui.button(label="Edit Link", style=discord.ButtonStyle.primary, emoji="🔗", row=0)
    async def edit_link_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = EditLinkModal(reminder=self.reminder)
        await interaction.response.send_modal(modal=modal)

    @discord.ui.button(label="Edit Time", style=discord.ButtonStyle.green, emoji="📅", row=1)
    async def edit_time_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = EditTimeModal(reminder=self.reminder)
        await interaction.response.send_modal(modal=modal)

    @discord.ui.button(label="Remove File", style=discord.ButtonStyle.danger, emoji="🔥", row=1)
    async def remove_file_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.reminder.remove_file()

        self.remove_item(self.get_remove_file_button())

        return await interaction.response.edit_message(attachments=[], view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def delete_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        name = self.reminder.name
        await self.reminder.delete()
        await interaction.response.edit_message(embed=EditErrorEmbed(error="Success", message=f"Reminder \"{name}\" has been deleted."), view=None)


class ReminderListView(View):
    _num_emojis = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣"}

    def __init__(self, *, reminder_embeds: list[ReminderEditEmbed], timeout=600):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.embeds = reminder_embeds
        self.page = 0
        self.per_page = 5
        self.total_pages = max(1, (len(self.embeds) + self.per_page - 1) // self.per_page)
        self.embed_buttons = []

        # Создаем embed-кнопки динамически
        for i in range(5):
            button = discord.ui.Button(
                emoji=self._num_emojis[i + 1],
                style=discord.ButtonStyle.gray,
                custom_id=f"embed_select_{i + 1}"
            )

            async def callback(interaction: discord.Interaction, index=i):
                start_idx = self.page * self.per_page
                actual_index = start_idx + index
                await self.show_reminder_details(interaction, self.embeds[actual_index].reminder_id)

            button.callback = callback
            self.add_item(button)
            self.embed_buttons.append(button)

        self.update_buttons()

    @staticmethod
    async def show_reminder_details(interaction: discord.Interaction, reminder_id: int):
        await interaction.response.defer()

        reminder = await Database.RemindersBD.get_reminder_by_id(reminder_id)
        view = ReminderEditView(reminder)
        embed = ReminderEditEmbed(reminder=reminder, embed_type="full")

        if reminder.file_name:
            file = discord.File(io.BytesIO(reminder.file), filename=reminder.file_name)
            await interaction.followup.edit_message(message_id=interaction.message.id, content="### Choose Field to Edit", embed=embed, view=view, file=file)
        else:
            await interaction.followup.edit_message(message_id=interaction.message.id, content="### Choose Field to Edit", embed=embed, view=view)

    def update_buttons(self):
        self.first_page.disabled = self.page == 0
        self.prev_page.disabled = self.page == 0
        self.next_page.disabled = self.page == self.total_pages - 1
        self.last_page.disabled = self.page == self.total_pages - 1
        self.page_indicator.label = f"{self.page + 1}/{self.total_pages}"

        start_idx = self.page * self.per_page
        for i, button in enumerate(self.embed_buttons):
            if start_idx + i < len(self.embeds):
                button.emoji = self._num_emojis[i + 1]
                button.disabled = False
                button.reminder_id = self.embeds[start_idx + i].reminder_id
            else:
                button.emoji = "❌"
                button.disabled = True
                button.reminder_id = None

    async def update_message(self, interaction: discord.Interaction):
        start_idx = self.page * self.per_page
        embeds = self.embeds[start_idx:start_idx + self.per_page]  # Берем 5 эмбедов)
        self.update_buttons()

        # Обновляем сообщение с эмбедами и view
        await interaction.response.edit_message(embeds=embeds, view=self)

    @discord.ui.button(label="<<", style=discord.ButtonStyle.blurple)
    async def first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page = 0
        await self.update_message(interaction)

    @discord.ui.button(label="<", style=discord.ButtonStyle.danger)
    async def prev_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        await self.update_message(interaction)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.gray, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=">", style=discord.ButtonStyle.green)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page = min(self.total_pages - 1, self.page + 1)
        await self.update_message(interaction)

    @discord.ui.button(label=">>", style=discord.ButtonStyle.blurple)
    async def last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page = self.total_pages - 1
        await self.update_message(interaction)
