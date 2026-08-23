import logging
from .config import LOVE_TRIGGER_ID, PERSONAL_TRIGGER_ID, PRIVATE_TRIGGER_ID, REPORT_TRIGGER_ID, SOBES_TRIGGER_ID
from .manager import create_room, delete_room

logger = logging.getLogger(__name__)

async def setup(bot):
    logger.info("[VOICE] Setting up voice extension")
    
    @bot.listen("on_voice_state_update")
    async def on_voice_state_update(member, before, after):
        logger.info(f"[VOICE] EVENT: member={member.name} ({member.id}), before={before.channel.id if before.channel else 'None'}, after={after.channel.id if after.channel else 'None'}")
        if getattr(member, "bot", False):
            return

        if after.channel:
            room_type = None
            if after.channel.id == PRIVATE_TRIGGER_ID:
                room_type = "private"
            elif after.channel.id == PERSONAL_TRIGGER_ID:
                room_type = "personal"
            # elif after.channel.id == LOVE_TRIGGER_ID:
            #     room_type = "love"
            elif after.channel.id == REPORT_TRIGGER_ID:
                room_type = "report"
            elif after.channel.id == SOBES_TRIGGER_ID:
                room_type = "sobes"
            
            if room_type:
                logger.info(f"[VOICE] TRIGGER DETECTED: room_type={room_type}")
                try:
                    await create_room(member, room_type)
                except Exception as e:
                    logger.exception(f"[VOICE] ERROR in create_room: {e}")

        if before.channel:
            await delete_room(before.channel)
    
    logger.info("[VOICE] MODULE LOADED")
