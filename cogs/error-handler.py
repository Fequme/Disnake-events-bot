import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import Bot


class Handler(commands.Cog):
    def __init__(self, client):
        self.client: Bot = client

    @commands.Cog.listener()
    async def on_slash_command_error(self, interaction: ApplicationCommandInteraction, error: Exception) -> None:

        if isinstance(error, commands.MissingRole):
            try:
                await interaction.response.defer(ephemeral=True)
            except disnake.InteractionResponded:
                pass
            embed = disnake.Embed()
            embed.description = f"> У вас недостаточно прав, чтобы использовать данную команду!"
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)
            return
        if isinstance(error, commands.MissingAnyRole):
            try:
                await interaction.response.defer(ephemeral=True)
            except disnake.InteractionResponded:
                pass
            missing_roles = []
            for role in error.missing_roles:
                if isinstance(role, int):
                    missing_roles.append(disnake.utils.get(
                        interaction.guild.roles, id=role).mention)
                if isinstance(role, str):
                    missing_roles.append(disnake.utils.get(
                        interaction.guild.roles, name=role).mention)
            embed = disnake.Embed()
            embed.description = f"> У вас недостаточно прав, чтобы использовать данную команду!"
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)
            return


def setup(client: Bot):
    client.add_cog(Handler(client))
    print('Cog: "error-handler" loaded!')
