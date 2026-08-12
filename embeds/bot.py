import discord
from discord import app_commands
from discord.ext import commands

class EmbedModal(discord.ui.Modal, title="Создание Embed"):
    title_in = discord.ui.TextInput(label="Заголовок", required=False, max_length=256)
    desc_in = discord.ui.TextInput(label="Описание", style=discord.TextStyle.paragraph, required=False, max_length=4000)
    color_in = discord.ui.TextInput(label="Цвет (HEX, например #FF0000)", required=False, max_length=7)
    footer_in = discord.ui.TextInput(label="Футер", required=False, max_length=200)
    image_url = discord.ui.TextInput(label="URL Картинки", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        color = discord.Color.default()
        if self.color_in.value:
            try:
                color = discord.Color(int(self.color_in.value.lstrip("#"), 16))
            except ValueError:
                pass
        
        embed = discord.Embed(
            title=self.title_in.value,
            description=self.desc_in.value,
            color=color
        )
        if self.footer_in.value:
            embed.set_footer(text=self.footer_in.value)
        if self.image_url.value:
            embed.set_image(url=self.image_url.value)
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Embed отправлен!", ephemeral=True)

class EmbedsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Создать embed сообщение через форму")
    async def embed(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmbedModal())

async def setup(bot):
    await bot.add_cog(EmbedsCog(bot))
