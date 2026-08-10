import discord
from discord import app_commands
from core.database import db_manager

class ShopView(discord.ui.View):
    def __init__(self, items, roles):
        super().__init__(timeout=60)
        self.items = items
        self.roles = roles
        
        options = []
        for item in items:
            options.append(discord.SelectOption(label=item['name'], value=f"item_{item['item_id']}", description=f"Цена: {item['price']}"))
        for role in roles:
            options.append(discord.SelectOption(label=role['name'], value=f"role_{role['listing_id']}", description=f"Цена: {role['price']}"))
        
        self.add_item(discord.ui.Select(placeholder="Выберите товар", options=options, custom_id="shop_select"))

async def setup(bot):
    @bot.tree.command(name="shop", description="Открыть магазин")
    async def shop(interaction: discord.Interaction):
        items = await db_manager.fetch("SELECT * FROM shop_items")
        roles = await db_manager.fetch("SELECT * FROM personal_role_listings WHERE is_sold = FALSE")
        
        if not items and not roles:
            return await interaction.response.send_message("Магазин пуст.", ephemeral=True)
        
        await interaction.response.send_message("Добро пожаловать в магазин!", view=ShopView(items, roles), ephemeral=True)
