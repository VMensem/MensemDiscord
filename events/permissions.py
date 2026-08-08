import discord
from .config import CONFIG

def is_event_manager(interaction: discord.Interaction) -> bool:
    if interaction.user.id == interaction.guild.owner_id: return True
    if interaction.user.guild_permissions.administrator: return True
    
    user_roles = {role.id for role in interaction.user.roles}
    if CONFIG["MANAGER_ROLE"] in user_roles: return True
    
    return any(role in user_roles for role in CONFIG["STAFF_ROLES"])
