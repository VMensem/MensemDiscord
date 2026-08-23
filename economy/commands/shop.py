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
        
        select = discord.ui.Select(placeholder="Выберите товар", options=options, custom_id="shop_select")
        select.callback = self.on_select
        self.add_item(select)

    async def on_select(self, interaction: discord.Interaction):
        value = interaction.data['values'][0]
        async with db_manager.transaction() as conn:
            # 1. Lock user balance
            user = await conn.fetchrow(
                "SELECT balance FROM users WHERE guild_id = $1 AND user_id = $2 FOR UPDATE",
                interaction.guild_id, interaction.user.id
            )
            
            if not user:
                return await interaction.response.send_message("Профиль не найден.", ephemeral=True)

            # 2. Extract item/role
            if value.startswith("item_"):
                item_id = int(value.split("_")[1])
                item = await conn.fetchrow("SELECT * FROM shop_items WHERE item_id = $1", item_id)
                if not item or user['balance'] < item['price']:
                    return await interaction.response.send_message("Недостаточно средств или товар отсутствует.", ephemeral=True)
                
                # Purchase logic
                await conn.execute("UPDATE users SET balance = balance - $1 WHERE guild_id = $2 AND user_id = $3", item['price'], interaction.guild_id, interaction.user.id)
                await conn.execute("INSERT INTO inventory (user_id, item_id) VALUES ($1, $2)", interaction.user.id, item_id)
                
            elif value.startswith("role_"):
                listing_id = int(value.split("_")[1])
                role = await conn.fetchrow("SELECT * FROM personal_role_listings WHERE listing_id = $1 AND is_sold = FALSE", listing_id)
                if not role or user['balance'] < role['price']:
                    return await interaction.response.send_message("Недостаточно средств или товар отсутствует.", ephemeral=True)
                
                # Purchase logic
                await conn.execute("UPDATE users SET balance = balance - $1 WHERE guild_id = $2 AND user_id = $3", role['price'], interaction.guild_id, interaction.user.id)
                await conn.execute("UPDATE personal_role_listings SET is_sold = TRUE WHERE listing_id = $1", listing_id)
                # Logic to grant role...
            
            await interaction.response.send_message("Покупка успешна!", ephemeral=True)

async def setup(bot):
    @bot.tree.command(name="shop", description="Открыть магазин")
    async def shop(interaction: discord.Interaction):
        items = await db_manager.fetch("SELECT * FROM shop_items")
        roles = await db_manager.fetch("SELECT * FROM personal_role_listings WHERE is_sold = FALSE")
        
        if not items and not roles:
            return await interaction.response.send_message("Магазин пуст.", ephemeral=True)
        
        await interaction.response.send_message("Добро пожаловать в магазин!", view=ShopView(items, roles), ephemeral=True)
