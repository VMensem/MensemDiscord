import discord
from discord.ui import View, Button
from .service import accept, reject_proposal

class ProposalView(View):
    def __init__(self, proposal_id: int, from_user_id: int, to_user_id: int, guild_id: int):
        super().__init__(timeout=86400)
        self.proposal_id = proposal_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.to_user_id:
            await interaction.response.send_message("Это предложение не для тебя.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: Button):
        try:
            await accept(self.proposal_id, self.guild_id)
            await interaction.response.edit_message(content=f"💕 {interaction.user.mention} принял предложение!", embed=None, view=None)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка: {e}", ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await reject_proposal(self.proposal_id)
        await interaction.response.edit_message(content=f"💔 Предложение отклонено.", embed=None, view=None)
