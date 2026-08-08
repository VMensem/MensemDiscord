from .config import SOBES_CATEGORY_ID, SOBES_PREFIX


async def create_sobes(member):
    category = member.guild.get_channel(SOBES_CATEGORY_ID)
    if category is None:
        raise RuntimeError("SOBES_CATEGORY_ID not found")

    channel = await member.guild.create_voice_channel(
        name=f"{SOBES_PREFIX} Собеседование",
        category=category,
        user_limit=2,
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
