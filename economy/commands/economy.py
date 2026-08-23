import discord
from discord import app_commands
from core.database import db_manager

async def setup(bot):
    @bot.tree.command(name="balance", description="Показать баланс")
    async def balance(interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        row = await db_manager.fetchrow(
            "SELECT balance, bank FROM users WHERE guild_id = $1 AND user_id = $2",
            interaction.guild_id, target.id
        )
        wallet = row["balance"] if row else 0
        bank = row["bank"] if row else 0
        await interaction.response.send_message(f"💰 Кошелёк: {wallet} Coins\n🏦 Банк: {bank} Coins", ephemeral=True)

    @bot.tree.command(name="daily", description="Получить ежедневную награду")
    async def daily(interaction: discord.Interaction):
        # Implementation with transaction for anti-abuse
        pass

    @bot.tree.command(name="work", description="Работать")
    async def work(interaction: discord.Interaction):
        # Implementation
        pass
