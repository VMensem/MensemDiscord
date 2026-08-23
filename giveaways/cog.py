# giveaways/cog.py

import discord
from discord.ext import commands
from discord import app_commands
import random

from .modals import GiveawayModal
from .database import get_giveaway, get_participants, add_winner, add_reroll_history, get_winners, deactivate_winner, finish_giveaway
from core.database import db_manager


class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="giveaway",
        description="Создать новый розыгрыш"
    )
    async def giveaway(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
            return
        
        await interaction.response.send_modal(GiveawayModal())

    @app_commands.command(
        name="reroll",
        description="Перевыбрать победителя розыгрыша"
    )
    @app_commands.describe(
        message_id="ID сообщения розыгрыша",
        user_id="ID пользователя (которого нужно заменить)"
    )
    async def reroll(self, interaction: discord.Interaction, message_id: str, user_id: discord.User = None):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
            return

        try:
            m_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Неверный формат ID.", ephemeral=True)
            return

        giveaway = await get_giveaway(m_id)
        if not giveaway or not giveaway["ended"]:
            await interaction.response.send_message("❌ Розыгрыш не найден или еще не завершен.", ephemeral=True)
            return

        await interaction.response.defer()
        
        async with db_manager.transaction() as conn:
            # Locking is implicit in a transaction with proper row selection in PG, 
            # but for safety in simple setups, we can do a select for update.
            # Here, we need to handle the logic carefully.
            
            # 1. Get all winners
            winners = await get_winners(m_id)
            
            if user_id and user_id.id not in winners:
                await interaction.followup.send("❌ Этот пользователь не является победителем.", ephemeral=True)
                return
            
            # 2. Get participants to find a new winner
            participants = await get_participants(m_id)
            
            # 3. New winner candidates: participants - current winners
            candidates = [p for p in participants if p not in winners]
            
            if not candidates:
                await interaction.followup.send("❌ Нет кандидатов для перевыбора.", ephemeral=True)
                return
                
            new_winner = random.choice(candidates)
            
            old_winner = user_id.id if user_id else winners[0]
            
            # 4. Update in DB
            await deactivate_winner(m_id, old_winner)
            await add_winner(m_id, new_winner, 0) # Position doesn't strictly matter for rerolls
            await add_reroll_history(m_id, old_winner, new_winner, interaction.user.id)
            
            # 5. Update Embed
            channel = self.bot.get_channel(giveaway["channel_id"])
            if channel:
                try:
                    message = await channel.fetch_message(m_id)
                    # Need to rebuild embed
                    new_winners = await get_winners(m_id)
                    
                    embed = message.embeds[0]
                    # Update winner field
                    embed.clear_fields()
                    embed.add_field(name="🎁 Приз", value=f"**{giveaway['prize']}**", inline=False)
                    embed.add_field(name="🏆 Победители", value="\n".join([f"<@{w}>" for w in new_winners]), inline=False)
                    
                    await message.edit(embed=embed)
                    await interaction.followup.send(f"✅ Успешно заменен победитель <@{old_winner}> на <@{new_winner}>!")
                except Exception as e:
                    await interaction.followup.send(f"❌ Ошибка при обновлении сообщения: {e}")
                    raise e

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
