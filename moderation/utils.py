import discord

def check_perms(interaction: discord.Interaction, target: discord.Member) -> str | None:
    if target == interaction.guild.owner:
        return "Нельзя наказывать владельца сервера."
    if target.id == interaction.client.user.id:
        return "Нельзя наказывать бота."
    if target.id == interaction.user.id:
        return "Нельзя наказывать себя."
    
    # Hierarchy check
    if target.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        return "У пользователя роль выше или равна вашей."
    if target.top_role >= interaction.guild.me.top_role:
        return "У пользователя роль выше или равна роли бота."
        
    return None

async def send_dm(target: discord.Member, embed: discord.Embed) -> bool:
    try:
        await target.send(embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False
