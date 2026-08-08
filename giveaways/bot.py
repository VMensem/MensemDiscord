from .manager import GiveawayManager


async def setup(bot):
    await bot.load_extension("giveaways.cog")

    async def on_giveaways_ready():
        if getattr(bot, "_giveaways_manager_started", False):
            return
        bot._giveaways_manager_started = True
        manager = GiveawayManager(bot)
        bot.loop.create_task(manager.start())
        print("OK Giveaways manager started")

    bot.add_listener(on_giveaways_ready, "on_ready")
    print("OK Giveaways module loaded")
