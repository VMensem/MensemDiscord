import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime, timedelta
from .database import init_db, get_config, set_config, add_suggestion, get_suggestion_by_message, update_suggestion, get_suggestion, get_recent_suggestions

# Словарь для хранения времени последнего создания идеи пользователем
last_idea_time = {}

class VoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Поддерживаю", style=discord.ButtonStyle.success, custom_id="suggest_up")
    async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "up")

    @discord.ui.button(label="Не поддерживаю", style=discord.ButtonStyle.danger, custom_id="suggest_down")
    async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "down")

    async def handle_vote(self, interaction: discord.Interaction, type):
        sug = get_suggestion_by_message(interaction.message.id)
        if not sug: return await interaction.response.send_message("Ошибка БД", ephemeral=True)
        
        up = json.loads(sug['votes_up'])
        down = json.loads(sug['votes_down'])
        uid = interaction.user.id
        
        if type == "up":
            if uid in up: up.remove(uid)
            else: 
                up.append(uid)
                if uid in down: down.remove(uid)
        else:
            if uid in down: down.remove(uid)
            else:
                down.append(uid)
                if uid in up: up.remove(uid)
        
        update_suggestion(sug['id'], votes_up=json.dumps(up), votes_down=json.dumps(down))
        
        embed = interaction.message.embeds[0]
        # Предполагаем, что поле "📊 Статистика" - это поле с индексом 4
        # Лучше найти поле по имени, но оставим как есть для совместимости
        embed.set_field_at(4, name="📊 Статистика", value=f"👍 {len(up)} | 👎 {len(down)}")
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("Голос учтен", ephemeral=True)

class SuggestionModal(discord.ui.Modal, title="Новая идея"):
    title_in = discord.ui.TextInput(label="Заголовок")
    desc_in = discord.ui.TextInput(label="Описание", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        chan_id = get_config("channel_id")
        if not chan_id: return await interaction.response.send_message("Канал не настроен!", ephemeral=True)
        chan = interaction.guild.get_channel(chan_id)
        if chan is None:
            return await interaction.response.send_message("Настроенный канал идей не найден.", ephemeral=True)
        
        sug_id = add_suggestion(interaction.user.id, chan_id, self.title_in.value, self.desc_in.value)
        embed = discord.Embed(title=f"💡 {self.title_in.value}", description=self.desc_in.value, color=discord.Color.red())
        embed.add_field(name="👤 Автор", value=interaction.user.mention)
        embed.add_field(name="📅 Дата", value=discord.utils.format_dt(discord.utils.utcnow()))
        embed.add_field(name="📊 Статус", value="🟡 На рассмотрении")
        embed.add_field(name="🆔 ID", value=str(sug_id))
        embed.add_field(name="📊 Статистика", value="👍 0 | 👎 0")
        
        msg = await chan.send(embed=embed, view=VoteView())
        update_suggestion(sug_id, message_id=msg.id)
        await interaction.response.send_message("Идея отправлена!", ephemeral=True)

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="idea-setup")
    @app_commands.checks.has_permissions(administrator=True)
    async def suggest_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
        set_config("channel_id", channel.id)
        set_config("admin_role_id", role.id)
        await interaction.response.send_message("Настроено!", ephemeral=True)

    @app_commands.command(name="idea-create")
    async def create(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        now = datetime.now()
        
        if user_id in last_idea_time and now - last_idea_time[user_id] < timedelta(days=1):
            remaining = timedelta(days=1) - (now - last_idea_time[user_id])
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            return await interaction.response.send_message(f"Ты уже предлагал идею сегодня. Попробуй через {hours}ч {minutes}м.", ephemeral=True)
        
        await interaction.response.send_modal(SuggestionModal())
        last_idea_time[user_id] = now

    @app_commands.command(name="idea-accept")
    @app_commands.checks.has_permissions(administrator=True)
    async def accept(self, interaction: discord.Interaction, id: int, comment: str):
        sug = get_suggestion(id)
        if not sug: return await interaction.response.send_message("Не найдено", ephemeral=True)
        update_suggestion(id, status="🟢 Принято", comment=comment, admin_id=interaction.user.id)
        
        channel = interaction.guild.get_channel(sug['channel_id'])
        if channel is None or not sug['message_id']:
            return await interaction.response.send_message("Сообщение идеи не найдено.", ephemeral=True)
        msg = await channel.fetch_message(sug['message_id'])
        embed = msg.embeds[0]
        # Находим поле с индексом 2, если порядок не менялся
        embed.set_field_at(2, name="📊 Статус", value="🟢 Принято")
        embed.add_field(name="👮 Администратор", value=interaction.user.mention)
        embed.add_field(name="💬 Комментарий", value=comment)
        await msg.edit(embed=embed, view=None)
        await interaction.response.send_message("Принято", ephemeral=True)

    @app_commands.command(name="idea-deny")
    @app_commands.checks.has_permissions(administrator=True)
    async def deny(self, interaction: discord.Interaction, id: int, reason: str):
        sug = get_suggestion(id)
        if not sug: return await interaction.response.send_message("Не найдено", ephemeral=True)
        update_suggestion(id, status="🔴 Отклонено", comment=reason, admin_id=interaction.user.id)
        
        channel = interaction.guild.get_channel(sug['channel_id'])
        if channel is None or not sug['message_id']:
            return await interaction.response.send_message("Сообщение идеи не найдено.", ephemeral=True)
        msg = await channel.fetch_message(sug['message_id'])
        embed = msg.embeds[0]
        embed.set_field_at(2, name="📊 Статус", value="🔴 Отклонено")
        embed.add_field(name="👮 Администратор", value=interaction.user.mention)
        embed.add_field(name="📄 Причина", value=reason)
        await msg.edit(embed=embed, view=None)
        await interaction.response.send_message("Отклонено", ephemeral=True)

    @app_commands.command(name="idea-delete")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete(self, interaction: discord.Interaction, id: int):
        sug = get_suggestion(id)
        if not sug: return await interaction.response.send_message("Не найдено", ephemeral=True)
        channel = interaction.guild.get_channel(sug['channel_id'])
        if channel is None or not sug['message_id']:
            return await interaction.response.send_message("Сообщение идеи не найдено.", ephemeral=True)
        msg = await channel.fetch_message(sug['message_id'])
        await msg.delete()
        await interaction.response.send_message("Удалено", ephemeral=True)

    @app_commands.command(name="idea-list")
    async def list(self, interaction: discord.Interaction):
        suggestions = get_recent_suggestions(limit=10)
        
        if not suggestions:
            return await interaction.response.send_message("Идей пока нет.", ephemeral=True)
            
        embed = discord.Embed(title="💡 Последние идеи", color=discord.Color.red())
        for sug in suggestions:
            embed.add_field(
                name=f"ID {sug['id']}: {sug['title']}",
                value=f"Статус: {sug['status']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    init_db()
    await bot.add_cog(Suggestions(bot))
    bot.add_view(VoteView())
