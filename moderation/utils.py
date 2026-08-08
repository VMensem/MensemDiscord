import discord


def check_perms(interaction: discord.Interaction, target: discord.Member) -> str | None:
    if target.id == interaction.client.user.id:
        return "Нельзя наказывать бота."
    if target.id == interaction.user.id:
        return "Нельзя наказывать себя."
    if target.top_role.position >= interaction.user.top_role.position and interaction.user.id != interaction.guild.owner_id:
        return "Пользователь выше вас по роли."
    return None


async def send_dm(target: discord.Member, embed: discord.Embed) -> bool:
    try:
        await target.send(embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False
