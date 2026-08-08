from .config import LOVE_CATEGORY_ID, LOVE_PREFIX


async def create_love(member):
    category = member.guild.get_channel(LOVE_CATEGORY_ID)
    if category is None:
        raise RuntimeError("LOVE_CATEGORY_ID not found")

    channel = await member.guild.create_voice_channel(
        name=f"{LOVE_PREFIX}{member.display_name} | в разработке",
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
