from .config import REPORT_CATEGORY_ID, REPORT_PREFIX


async def create_report(member):
    category = member.guild.get_channel(REPORT_CATEGORY_ID)
    if category is None:
        raise RuntimeError("REPORT_CATEGORY_ID not found")

    channel = await member.guild.create_voice_channel(
        name=f"{REPORT_PREFIX} Разбирательства",
        category=category,
        user_limit=3,
    )

    await channel.set_permissions(
        member,
        manage_channels=True,
        move_members=True,
        mute_members=True,
        deafen_members=True,
        connect=True,
    )

    return channel
