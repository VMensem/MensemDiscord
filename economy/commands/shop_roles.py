import discord
from discord import app_commands
from core.database import db_manager

class RoleCreateModal(discord.ui.Modal, title="Создание роли"):
    name = discord.ui.TextInput(label="Название роли")
    price = discord.ui.TextInput(label="Цена")
    color = discord.ui.TextInput(label="HEX Цвет (например #FF0000)")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            price = int(self.price.value)
            if not self.color.value.startswith("#"):
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("Ошибка в данных.", ephemeral=True)
            
        role = await interaction.guild.create_role(name=self.name.value, color=discord.Color.from_str(self.color.value))
        
        await db_manager.execute(
            "INSERT INTO personal_role_listings (guild_id, seller_id, role_id, name, price) VALUES ($1, $2, $3, $4, $5)",
            interaction.guild_id, interaction.user.id, role.id, self.name.value, price
        )
        await interaction.response.send_message(f"Роль {role.mention} выставлена на продажу!", ephemeral=True)

async def setup(bot):
    @bot.tree.command(name="role-create", description="Выставить свою роль на продажу")
    async def role_create(interaction: discord.Interaction):
        await interaction.response.send_modal(RoleCreateModal())
    
    @bot.tree.command(name="role-buy", description="Купить роль")
    async def role_buy(interaction: discord.Interaction, listing_id: int):
        async with db_manager.pool.acquire() as conn:
            async with conn.transaction():
                listing = await conn.fetchrow(
                    "SELECT * FROM personal_role_listings WHERE listing_id = $1 AND is_sold = FALSE FOR UPDATE",
                    listing_id
                )
                if not listing:
                    return await interaction.response.send_message("Роль не найдена или уже продана.", ephemeral=True)
                
                if listing["seller_id"] == interaction.user.id:
                    return await interaction.response.send_message("Нельзя купить свою роль.", ephemeral=True)
                
                buyer = await conn.fetchrow(
                    "SELECT balance FROM users WHERE guild_id = $1 AND user_id = $2 FOR UPDATE",
                    interaction.guild_id, interaction.user.id
                )
                if not buyer or buyer["balance"] < listing["price"]:
                    return await interaction.response.send_message("Недостаточно средств.", ephemeral=True)
                
                await conn.execute(
                    "UPDATE users SET balance = balance - $1 WHERE guild_id = $2 AND user_id = $3",
                    listing["price"], interaction.guild_id, interaction.user.id
                )
                await conn.execute(
                    "UPDATE personal_role_listings SET is_sold = TRUE WHERE listing_id = $1",
                    listing_id
                )
                await conn.execute(
                    "INSERT INTO transactions (guild_id, user_id, type, amount, reason) VALUES ($1, $2, 'shop_role', $3, $4)",
                    interaction.guild_id, interaction.user.id, listing["price"], f"Bought role {listing['name']}"
                )
        
        role = interaction.guild.get_role(listing["role_id"])
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Успешно куплена роль {role.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message("Роль не найдена на сервере.", ephemeral=True)
