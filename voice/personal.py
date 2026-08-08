from .config import PERSONAL_CATEGORY_ID, PERSONAL_PREFIX


async def create_personal(member):
    category = member.guild.get_channel(PERSONAL_CATEGORY_ID)
    if category is None:
        raise RuntimeError("PERSONAL_CATEGORY_ID not found")

    channel = await member.guild.create_voice_channel(
        name=f"{PERSONAL_PREFIX}{member.display_name}",
        category=category,
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
