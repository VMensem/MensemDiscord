import discord
from discord.ui import View, Select, Button
from core.database import db_manager

class ShopView(View):
    def __init__(self, items):
        super().__init__(timeout=60)
        self.items = items
        
        # Populate select with shop items
        options = []
        for item in items:
            options.append(discord.SelectOption(label=item['name'], value=str(item['item_id']), description=f"Цена: {item['price']}"))
        
        self.add_item(Select(placeholder="Выберите товар", options=options, custom_id="shop_select"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Atomic purchase logic will be here
        return True
