from .config import LOVE_TRIGGER_ID, PERSONAL_TRIGGER_ID, PRIVATE_TRIGGER_ID, REPORT_TRIGGER_ID, SOBES_TRIGGER_ID
from .manager import create_room, delete_room


def setup(bot):
    @bot.listen()
    async def on_voice_state_update(member, before, after):
        if getattr(member, "bot", False):
            return

        if after.channel:
            if after.channel.id == PRIVATE_TRIGGER_ID:
                await create_room(member, "private")
            elif after.channel.id == PERSONAL_TRIGGER_ID:
                await create_room(member, "personal")
            elif after.channel.id == LOVE_TRIGGER_ID:
                await create_room(member, "love")
            elif after.channel.id == REPORT_TRIGGER_ID:
                await create_room(member, "report")
            elif after.channel.id == SOBES_TRIGGER_ID:
                await create_room(member, "sobes")

        if before.channel:
            await delete_room(before.channel)
