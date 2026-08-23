from discord import app_commands
import discord
from ..services.economy import get_balance
from ..embeds import create_economy_embed

async def setup(bot):
    @bot.tree.command(name="balance", description="Показать баланс")
    async def balance(interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        wallet, bank = await get_balance(interaction.guild_id, target.id)
        
        embed = create_economy_embed(f"Баланс {target.display_name}", 
                                     f"💰 Кошелёк: {wallet} Coins\n🏦 Банк: {bank} Coins")
        await interaction.response.send_message(embed=embed)
