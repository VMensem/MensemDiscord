import discord
from discord import app_commands
from core.database import db_manager

async def setup(bot):
    @bot.tree.command(name="pay", description="Перевести деньги пользователю")
    async def pay(interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("Сумма должна быть положительной.", ephemeral=True)
        if member == interaction.user:
            return await interaction.response.send_message("Нельзя перевести деньги самому себе.", ephemeral=True)
        
        async with db_manager.pool.acquire() as conn:
            async with conn.transaction():
                # Check sender balance
                sender = await conn.fetchrow(
                    "SELECT balance FROM users WHERE guild_id = $1 AND user_id = $2 FOR UPDATE",
                    interaction.guild_id, interaction.user.id
                )
                if not sender or sender["balance"] < amount:
                    return await interaction.response.send_message("Недостаточно средств.", ephemeral=True)
                
                # Update sender
                await conn.execute(
                    "UPDATE users SET balance = balance - $1 WHERE guild_id = $2 AND user_id = $3",
                    amount, interaction.guild_id, interaction.user.id
                )
                # Update receiver
                await conn.execute(
                    """
                    INSERT INTO users (guild_id, user_id, balance) 
                    VALUES ($1, $2, $3) 
                    ON CONFLICT (guild_id, user_id) DO UPDATE SET balance = users.balance + $3
                    """,
                    interaction.guild_id, member.id, amount
                )
        
        await interaction.response.send_message(f"Переведено {amount} пользователю {member.mention}.", ephemeral=True)
