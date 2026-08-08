from .config import PRIVATE_CATEGORY_ID, PRIVATE_PREFIX


async def create_private(member):
    category = member.guild.get_channel(PRIVATE_CATEGORY_ID)
    if category is None:
        raise RuntimeError("PRIVATE_CATEGORY_ID not found")

    channel = await member.guild.create_voice_channel(
        name=f"{PRIVATE_PREFIX}{member.display_name}",
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
