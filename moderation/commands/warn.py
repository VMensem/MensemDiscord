import discord
from ..database import add_case
from ..utils import check_perms, send_dm
from ..embeds import create_embed

async def setup(bot):
    @bot.tree.command(name="warn", description="Выдать предупреждение")
    async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
        error = check_perms(interaction, member)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)
        
        case_id = add_case(interaction.guild_id, member.id, interaction.user.id, "WARN", reason)
        
        embed = create_embed(f"Case #{case_id:04d} | Предупреждение", f"Участник: {member.mention}\nПричина: {reason}")
        await interaction.response.send_message(embed=embed)
        await send_dm(member, embed)
