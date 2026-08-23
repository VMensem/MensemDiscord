import discord
from discord.ext import commands
from discord import app_commands
from .service import is_user_in_relationship, propose, accept, divorce as divorce_service
from .database import create_proposal, reject_proposal
from .views import ProposalView
from voice.manager import create_room
import datetime

class Love(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="marry", description="Предложить руку и сердце")
    async def marry(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user == user:
            return await interaction.response.send_message("Нельзя жениться на самом себе.", ephemeral=True)
        
        try:
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
            proposal_id = await create_proposal(interaction.guild_id, interaction.user.id, user.id, expires_at)
            
            view = ProposalView(proposal_id, interaction.user.id, user.id, interaction.guild_id)
            await interaction.response.send_message(f"{user.mention}, {interaction.user.mention} предлагает тебе руку и сердце! 💍", view=view)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)

    @app_commands.command(name="love", description="Профиль отношений")
    async def love_profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        rel = await is_user_in_relationship(interaction.guild_id, target.id)
        if not rel:
            return await interaction.response.send_message("❌ Пользователь не состоит в отношениях.", ephemeral=True)
        
        partner_id = rel['user2_id'] if rel['user1_id'] == target.id else rel['user1_id']
        partner = interaction.guild.get_member(partner_id)
        partner_mention = partner.mention if partner else f"ID: {partner_id}"

        embed = discord.Embed(title="💕 Love Profile", color=discord.Color.red())
        embed.add_field(name="Пара", value=f"{target.mention} ❤️ {partner_mention}")
        embed.add_field(name="Вместе с", value=rel['created_at'].strftime("%d.%m.%Y"))
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="love-room", description="Создать Love Room")
    async def love_room(self, interaction: discord.Interaction):
        rel = await is_user_in_relationship(interaction.guild_id, interaction.user.id)
        if not rel:
            return await interaction.response.send_message("Love Room доступна только участникам пары.", ephemeral=True)
        
        # Integration with Voice
        await create_room(interaction.user, 'love')
        await interaction.response.send_message("Love Room создана!", ephemeral=True)

    @app_commands.command(name="love-divorce", description="Развестись")
    async def divorce(self, interaction: discord.Interaction):
        rel = await is_user_in_relationship(interaction.guild_id, interaction.user.id)
        if not rel:
            return await interaction.response.send_message("❌ Ты не состоишь в отношениях.", ephemeral=True)
        
        await divorce_service(rel['relationship_id'])
        await interaction.response.send_message("💔 Вы расстались.")

async def setup(bot):
    await bot.add_cog(Love(bot))
