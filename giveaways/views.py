import discord

from .database import (
    add_participant,
    get_participants
)


RED = discord.Color.from_rgb(220, 20, 60)


class ParticipantsView(discord.ui.View):

    def __init__(self, users):
        super().__init__(timeout=60)

        self.users = users
        self.page = 0


    def get_page(self):

        per_page = 10

        start = self.page * per_page
        end = start + per_page

        return self.users[start:end]


    def build_embed(self):

        embed = discord.Embed(
            title="👥 Участники розыгрыша",
            color=RED
        )

        users = self.get_page()


        if not users:
            embed.description = (
                "Пока никто не участвует 😢"
            )

        else:

            text = ""

            for index, user in enumerate(
                users,
                start=self.page * 10 + 1
            ):
                text += f"**{index}.** <@{user}>\n"


            embed.description = text


        pages = max(
            1,
            (len(self.users) + 9) // 10
        )

        embed.set_footer(
            text=f"Страница {self.page + 1}/{pages} • Всего {len(self.users)}"
        )

        return embed



    @discord.ui.button(
        label="⬅️",
        style=discord.ButtonStyle.gray
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.page > 0:
            self.page -= 1


        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )



    @discord.ui.button(
        label="➡️",
        style=discord.ButtonStyle.gray
    )
    async def next(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        pages = max(
            1,
            (len(self.users)+9)//10
        )


        if self.page < pages - 1:
            self.page += 1


        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )





class GiveawayView(discord.ui.View):

    def __init__(self, message_id):

        super().__init__(
            timeout=None
        )

        self.message_id = message_id



    @discord.ui.button(
        label="🎉 Участвовать",
        style=discord.ButtonStyle.danger,
        custom_id="giveaway_join"
    )
    async def join(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):


        result = await add_participant(
            self.message_id,
            interaction.user.id
        )


        if result:

            await interaction.response.send_message(
                "❤️ Вы успешно участвуете в розыгрыше!",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                "⚠️ Вы уже участвуете!",
                ephemeral=True
            )





    @discord.ui.button(
        label="👥 Участники",
        style=discord.ButtonStyle.secondary,
        custom_id="giveaway_users"
    )
    async def users(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        users = await get_participants(
            self.message_id
        )


        view = ParticipantsView(users)


        await interaction.response.send_message(
            embed=view.build_embed(),
            view=view,
            ephemeral=True
        )