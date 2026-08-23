import discord
from discord.ui import View, Button
from core.database import db_manager

class ClanTopView(View):
    def __init__(self, clans):
        super().__init__(timeout=60)
        self.clans = clans
        self.page = 0
        self.items_per_page = 5

    def get_embed(self):
        embed = discord.Embed(title="🏆 Топ кланов", color=discord.Color.gold())
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        for i, clan in enumerate(self.clans[start:end], start=start + 1):
            embed.add_field(name=f"{i}. {clan['name']} [{clan['tag']}]", 
                            value=f"Уровень: {clan['level']} | XP: {clan['xp']} | Участники: {clan['member_count']}", 
                            inline=False)
        return embed

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.primary)
    async def prev(self, interaction: discord.Interaction, button: Button):
        self.page = max(0, self.page - 1)
        await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Вперёд", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: Button):
        self.page = min((len(self.clans) - 1) // self.items_per_page, self.page + 1)
        await interaction.response.edit_message(embed=self.get_embed())
