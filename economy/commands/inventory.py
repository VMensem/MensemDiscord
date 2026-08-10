import discord
from discord import app_commands
from core.database import db_manager

async def setup(bot):
    @bot.tree.command(name="inventory", description="Показать ваш инвентарь")
    async def inventory(interaction: discord.Interaction):
        # Query personal roles for user
        roles = await db_manager.fetch(
            "SELECT name FROM personal_role_listings WHERE guild_id = $1 AND is_sold = TRUE AND seller_id = $2", # Needs better tracking of ownership
            interaction.guild_id, interaction.user.id
        )
        if not roles:
            return await interaction.response.send_message("Инвентарь пуст.", ephemeral=True)
            
        items = "\n".join([r['name'] for r in roles])
        await interaction.response.send_message(f"Ваш инвентарь:\n{items}", ephemeral=True)
