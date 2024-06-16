import datetime
import disnake
from disnake.enums import ButtonStyle
from disnake.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import asyncio
import re
import config
from config import *


mongodb_url = (events['mongodb_url'])
cluster = AsyncIOMotorClient(mongodb_url)
eventvoice = cluster.GitHubFequme.voices
close_bans = cluster.GitHubFequme.event_ban
pred_system = cluster.GitHubFequme.pred_system
staff = cluster.GitHubFequme.profile
staffwarns = cluster.GitHubFequme.warns
is_event = {}


def convert_time(seconds: int) -> str:
    minutes, _ = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours >= 24:
        days, hours = divmod(hours, 24)
        if days >= 7:
            weeks, days = divmod(days, 7)
            return "%sнед. %sд." % (weeks, days)
        return "%sд. %sч." % (days, hours)
    return "%sч. %sмин." % (hours, minutes)


class ManageEvent(disnake.ui.View):
    def __init__(self, client, inter, text_event_channel, voice_event_channel, inform, chat, category, message_log: disnake.Message, start_time, view, msg):
        super().__init__(timeout=None)
        self.client = client
        self.inter = inter
        self.message_log = message_log
        self.start_time = start_time
        self.text_event_channel = text_event_channel
        self.voice_event_channel = voice_event_channel
        self.category = category
        self.inform = inform
        self.chat = chat
        self.view = view
        self.msg = msg
        self.check_bans.start()

    async def interaction_check(self, interaction):
        return interaction.user == self.inter.author

    @tasks.loop(seconds=5)
    async def check_bans(self):
        async for doc in close_bans.find({}):
            if doc['close_ban'] <= datetime.datetime.now():
                await close_bans.delete_one({"_id": doc['_id']})
                member = self.inter.guild.get_member(doc['_id'])
                if not member:
                    continue
                ev_ban = disnake.utils.get(
                    self.inter.guild.roles, id=int(events['ban_id_role']))
                await member.remove_roles(ev_ban)

    @disnake.ui.button(label="Закрыть чат", style=ButtonStyle.gray, row=1)
    async def close_chat(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.chat.set_permissions(interaction.author.guild.default_role, send_messages=False, read_message_history=False, read_messages=False)
        embed = disnake.Embed()
        embed.description = f"> Чат был успешно закрыт, теперь писать можете только вы!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label="Открыть чат",  style=ButtonStyle.gray, row=1)
    async def open_chat(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.chat.set_permissions(interaction.author.guild.default_role, send_messages=True, read_message_history=True, read_messages=True)
        embed = disnake.Embed()
        embed.description = f"> Чат был успешно открыт, теперь писать могут все!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label='Закрыть войс', style=disnake.ButtonStyle.gray, row=1)
    async def her(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        overwrites = self.voice_event_channel.overwrites_for(
            interaction.guild.default_role)
        overwrites.update(connect=False)
        await self.voice_event_channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        embed = disnake.Embed()
        embed.description = f"> Войс успешно закрыт!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label='Открыть войс', style=disnake.ButtonStyle.gray, row=1)
    async def open_voice(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        overwrites = self.voice_event_channel.overwrites_for(
            interaction.guild.default_role)
        overwrites.update(connect=None)
        await self.voice_event_channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        embed = disnake.Embed()
        embed.description = f"> Войс успешно открыт!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label='Замутить всех', style=disnake.ButtonStyle.gray, row=2)
    async def mute_members(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        for member in self.voice_event_channel.members:
            try:
                await member.edit(mute=True)
            except Exception:
                pass
        embed = disnake.Embed()
        embed.description = f"> Теперь разговаривать в войсе нельзя!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label='Размутить всех', style=disnake.ButtonStyle.gray, row=2)
    async def un_mute_members(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        for member in self.voice_event_channel.members:
            try:
                await member.edit(mute=False)
            except Exception:
                pass
        embed = disnake.Embed()
        embed.description = f"> Теперь разговаривать в войсе можно!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label='Изменить слоты канала', style=disnake.ButtonStyle.gray, row=2)
    async def edit_limit(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer(ephemeral=True)

        def check(_: disnake.Message) -> bool:
            return _.author == interaction.author and _.channel == interaction.channel and _.content.isdigit() \
                and int(_.content) < 100

        embed = disnake.Embed()
        embed.description = f"> Укажите какой лимит вы хотите поставить (0 - 99)!"
        embed.color = 0x2f3136
        msg = await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            message = await interaction.client.wait_for('message', check=check, timeout=60)
            try:
                await message.delete()
            except disnake.NotFound:
                pass
            limit = int(message.content)

        except asyncio.TimeoutError:
            embed = disnake.Embed()
            embed.description = f"> {interaction.author.mention}, время **вышло**!"
            embed.color = 0x2f3136
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        if limit > 99:
            print(99)
            embed = disnake.Embed()
            embed.description = f"> Вы привысили лимит. Укажите число от 0 до 99"
            embed.color = 0x2f3136
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await self.voice_event_channel.edit(user_limit=limit)

        embed = disnake.Embed()
        embed.description = f"> Успешно был выставлено ограничение слотов на значение - ``{limit}``"
        embed.color = 0x2f3136
        await msg.edit(embed=embed)

    @disnake.ui.button(label="Выгнать пользователя", style=ButtonStyle.gray, row=2)
    async def kick_membe(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        embed = disnake.Embed()
        embed.description = f"> Укажите пользователя!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)

        def check(m):
            return m.channel == interaction.channel and m.author == interaction.author

        msg = await self.client.wait_for("message", check=check)
        a = msg.content
        a = a.replace("<", "")
        a = a.replace(">", "")
        a = a.replace("@", "")
        try:
            member = interaction.guild.get_member(int(a))
            if not member.id == interaction.author.id:
                if member.voice and member.voice.channel == self.voice_event_channel:
                    await self.text_event_channel.set_permissions(member, view_channel=False)
                    await self.voice_event_channel.set_permissions(member, view_channel=False)
                    # await self.text_event_channel.set_permissions(member, send_messages=False)
                    await member.move_to(None)
                    await msg.delete()
                    embed = disnake.Embed()
                    embed.description = f"> Пользователь был выгнан с ивента!"
                    embed.color = 0x2f3136
                    await interaction.send(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed()
                    embed.description = f"> Пользователь должен находится в голосовом канале события!"
                    embed.color = 0x2f3136
                    await interaction.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed()
                embed.description = f"> Нельзя выгнать самого себя!"
                embed.color = 0x2f3136
                await interaction.send(embed=embed, ephemeral=True)
        except:
            embed = disnake.Embed()
            embed.description = f"> Что-то пошло не так!"
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)

    @disnake.ui.button(label="ID-пользователей", style=ButtonStyle.grey, row=2)
    async def giveallmembers(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        members = []
        for member in self.voice_event_channel.members:
            if member.id != interaction.author.id:
                members.append(member.id)

        emb = disnake.Embed(
            description="\n"
        )
        emb.set_author(name="ID-пользователей на вашем событии")
        if interaction.guild.icon is not None:
            emb.set_footer(text="💣 GitHub Fequme", icon_url=interaction.guild.icon)
        else:
            emb.set_footer(text="💣 GitHub Fequme")
        emb.set_thumbnail(interaction.author.display_avatar)
        emb.color = 0x2f3136

        for count, member in enumerate(members):
            emb.description += f'**Названия ивента: {event_name}**\n\n **{count + 1}.** <@{member}> | {member} \n'

        embed = disnake.Embed()
        embed.description = f"> Список был отправлен вам в личные сообщения!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)
        try:
            await interaction.author.send(embed=emb)
        except:
            pass

    @disnake.ui.button(label="Выдать фол", style=ButtonStyle.red, row=3)
    async def fol(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()

        def check(msg: disnake.Message) -> bool:
            return msg.author == interaction.user and msg.channel == interaction.channel \
                and msg.mentions

        embed = disnake.Embed()
        embed.description = f"> Упомяните участника!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)
        try:
            message: disnake.Message = await interaction.client.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            embed = disnake.Embed()
            embed.description = f"> Время прошло!"
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)
            return
        await message.delete(delay=1)
        try:
            member = await interaction.guild.fetch_member(message.mentions[0].id)
        except disnake.NotFound:
            embed = disnake.Embed()
            embed.description = f"> Нету такого участника в гильдии!"
            embed.color = 0x2f3136
            return await interaction.send(embed=embed, ephemeral=True)
        if await pred_system.find_one({"_id": member.id}) is None:
            await pred_system.insert_one({"_id": member.id, "leader": interaction.author.id, "warns": 0})
        if await close_bans.find_one({"_id": member.id}):
            return await interaction.send('У пользователя уже есть ивент бан!', ephemeral=True)
        if (await pred_system.find_one({"_id": member.id}))['warns'] == 3:
            return await interaction.send('У пользователя уже есть 3 фола!', ephemeral=True)
        await pred_system.update_one({"_id": member.id}, {"$inc": {"warns": 1}})
        count_warn = (await pred_system.find_one({"_id": member.id}))['warns']
        if count_warn < 3:
            if await staff.find_one({"id": interaction.author.id}) is None:
                await staff.insert_one({
                    "id": interaction.author.id,
                    "online": 0,
                    "warns": 0,
                    "events": 0,
                    "bans": 0,
                    "fols": 1,
                    "week_online": 0,
                    "week_events": 0,
                    "week_bans": 0,
                    "week_fols": 4
                })
            else:
                await staff.update_one({"id": interaction.author.id}, {"$inc": {"fols": 1}})
                await staff.update_one({"id": interaction.author.id}, {"$inc": {"week_fols": 1}})

            emb = disnake.Embed(color=0x2f3136)
            emb.set_author(name=f'Вам был выдан фол',
                           icon_url='https://cdn-icons-png.flaticon.com/512/594/594646.png')
            emb.add_field(
                name="Кто выдал", value=f"```{interaction.author}```")
            emb.add_field(
                name="Название ивента", value=f"```{event_name}```", inline=True)
            emb.add_field(
                name="Фолы", value=f"```{count_warn}/3```", inline=True)
            emb.set_thumbnail(url=interaction.author.display_avatar)
            try:
                msg_mem = await member.send(embed=emb)

            except disnake.Forbidden:
                pass
            try:
                await member.edit(nick=f'{count_warn}/3 ф {member.name}')
            except disnake.Forbidden:
                pass
            embed = disnake.Embed()
            embed.description = f"> Участнику был выдан {count_warn}/3 фолов!"
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)

            def check(_: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
                return not (member in self.voice_event_channel.members)
            await interaction.client.wait_for('voice_state_update', check=check)
            try:
                await member.edit(nick=None)
            except disnake.Forbidden:
                pass
            return

        def check(msg: disnake.Message) -> bool:
            return msg.author == interaction.user and msg.channel == interaction.channel \
                and msg.content.isdigit()

        embed = disnake.Embed()
        embed.description = f"> Укажите время (в днях)!"
        embed.color = 0x2f3136
        await interaction.send(embed=embed, ephemeral=True)
        try:
            message: disnake.Message = await interaction.client.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            embed = disnake.Embed()
            embed.description = f"> Время прошло!"
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)
            return
        await message.delete(delay=1)
        # Event Ban
        ev_ban = disnake.utils.get(
            interaction.guild.roles, id=int(events['ban_id_role']))
        await member.add_roles(ev_ban, reason='3 фола')
        await member.edit(voice_channel=None)
        date_expired = datetime.datetime.now() + datetime.timedelta(days=int(message.content))
        if await close_bans.find_one({"_id": member.id}) is None:
            await close_bans.insert_one({"_id": member.id, "close_ban": date_expired})
        await close_bans.update_one({"_id": member.id}, {"$set": {"close_ban": date_expired}})
        await interaction.send(f'event бан был успешно выдан пользовотелю {member.mention}', ephemeral=True)
        emb = disnake.Embed(color=0x2f3136)
        emb.set_author(name=f'Вам был выдан ивент бан',
                       icon_url='https://cdn-icons-png.flaticon.com/512/6715/6715772.png')
        emb.add_field(
            name="Кто выдал", value=f"```{interaction.author}```")
        emb.add_field(
            name="Название ивента", value=f"```{event_name}```", inline=True)
        emb.add_field(
            name="Время", value=f"```{message.content}days```", inline=True)
        emb.add_field(
            name="Причина", value=f"```3 фола```", inline=True)
        emb.set_thumbnail(url=interaction.author.display_avatar)
        try:
            msg_mem = await member.send(embed=emb)
        except disnake.Forbidden:
            pass
        try:
            await member.edit(nick=f'3/3 ф {member.name}')
        except disnake.Forbidden:
            pass
        log_channel = interaction.bot.get_channel(
            int(events['log_ban_chennel']))
        emb = disnake.Embed(color=0x2f3136)
        emb.set_author(name=f'Логи — Ивент банов',
                       icon_url='https://cdn-icons-png.flaticon.com/512/6715/6715772.png')
        emb.add_field(
            name="Кто выдал", value=f"```{interaction.author}```")
        emb.add_field(
            name="Кому выдал", value=f"```{member._user}```")
        emb.add_field(
            name="Время", value=f"```{message.content}days```")
        emb.add_field(
            name="Причина", value=f"```3 фола```")
        emb.set_thumbnail(url=interaction.author.display_avatar)
        await log_channel.send(embed=emb)

        if await staff.find_one({"id": interaction.author.id}) is None:
            await staff.insert_one({
                "id": interaction.author.id,
                "online": 0,
                "warns": 0,
                "events": 0,
                "bans": 1,
                "fols": 0,
                "week_online": 0,
                "week_events": 0,
                "week_bans": 0,
                "week_fols": 0
            })
        else:
            await staff.update_one({"id": interaction.author.id}, {"$inc": {"bans": 1}})
            await staff.update_one({"id": interaction.author.id}, {"$inc": {"week_bans": 1}})

        def check(_: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
            return not (member in self.voice_event_channel.members)
        await interaction.client.wait_for('voice_state_update', check=check)
        try:
            await member.edit(nick=None)
        except disnake.Forbidden:
            pass

    @disnake.ui.button(label="Завершить ивент", style=ButtonStyle.red, row=3)
    async def close_event(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        global is_event
        await self.text_event_channel.delete()
        await self.voice_event_channel.delete()
        await self.inform.delete()
        await self.chat.delete()
        await self.category.delete()
        try:
            await interaction.author.edit(nick=None)
        except disnake.Forbidden:
            pass
        embed_ = disnake.Embed(color=12836075)
        embed_.set_author(name=f'Логи — Ивентов',
                          icon_url='https://cdn-icons-png.flaticon.com/512/8633/8633160.png')
        embed_.add_field(
            name="Ивент", value=f"```{event_name}```")
        embed_.add_field(
            name="Ведущий", value=f"```{interaction.author}```")
        seconds = int((datetime.datetime.now() - self.start_time).seconds)
        embed_.add_field(
            name='Длительность', value=f'```{convert_time(seconds)}```')
        embed_.set_footer(
            text=f'Ивент начался в {self.start_time.strftime(r"%H:%M")}')
        # embed_.description = f'**Ивент** {event_name} **успешно** закончен в {datetime.datetime.now().strftime(r"%H:%M")}.'
        await self.message_log.edit(embed=embed_)

        self.view.children[0].disabled = True
        self.view.children[0].label = "Ивент окончен"
        await self.msg.edit(view=self.view)
        self.view.stop()
        is_event.update({interaction.author.id: False})
        await pred_system.delete_many({"leader": interaction.author.id})
        await eventvoice.delete_one({"voice": self.voice_event_channel.id})
        async for doc in pred_system.find({"leader": interaction.author.id}):
            try:
                member = await interaction.guild.fetch_member(doc['_id'])
            except disnake.NotFound:
                continue
            await member.edit(nick=None)


class Weekd(disnake.ui.View):
    def __init__(self, mem):
        self.member = mem
        super().__init__(timeout=None)

    @disnake.ui.button(label="За неделю", style=ButtonStyle.grey)
    async def fweeekdd(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        stafft = await staff.find_one({"id": self.member.id})
        if stafft:
            embed = disnake.Embed()
            embed.set_author(name=f"Статистика {self.member} за неделю")
            embed.color = 0x2f3136
            embed.set_thumbnail(url=interaction.author.display_avatar)

            embed.add_field(
                name="Онлайн",
                value=f"```{convert_time(stafft['week_online'])}```",
                inline=True
            )

            embed.add_field(
                name="Проведено ивентов",
                value=f"```{stafft['week_events']}```",
                inline=True
            )

            embed.add_field(
                name="Выдано блокировок",
                value=f"```{stafft['week_bans']}```",
                inline=True
            )

            embed.add_field(
                name="Выдано фолов",
                value=f"```{stafft['week_fols']}```",
                inline=True
            )

            await interaction.response.edit_message(embed=embed)
        else:
            await staff.insert_one({
                "id": self.member.id,
                "online": 0,
                "warns": 0,
                "events": 1,
                "bans": 0,
                "fols": 0,
                "week_online": 0,
                "week_events": 0,
                "week_bans": 0,
                "week_fols": 0
            })

            embed = disnake.Embed()
            embed.set_author(name=f"Статистика {self.member} за неделю")
            embed.color = 0x2f3136
            embed.set_thumbnail(url=interaction.author.display_avatar)

            embed.add_field(
                name="Онлайн",
                value=f"```{convert_time(stafft['week_online'])}```",
                inline=True
            )

            embed.add_field(
                name="Проведено ивентов",
                value=f"```{stafft['week_events']}```",
                inline=True
            )

            embed.add_field(
                name="Выдано блокировок",
                value=f"```{stafft['week_bans']}```",
                inline=True
            )

            embed.add_field(
                name="Выдано фолов",
                value=f"```{stafft['week_fols']}```",
                inline=True
            )

            await interaction.response.edit_message(embed=embed)


class Rules(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Правила ивента", style=ButtonStyle.grey)
    async def ffff(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        embed = disnake.Embed()
        embed.color = 0x2f3136
        embed.set_author(name="Правила ивента")
        embed.description = "Несоблюдение этих правил влечет за собой систему 3-х предупреждений и ивент-бан. Незнание правил ивентов не освобождает вас от ответственности.\n\n> 1.1 На ивенте работают все правила сервера. Запрещены никнеймы, аватарки и теги оскорбительных и провокационных слов, реклама в любом виде, в том числе размещение ссылок и названий сторонних турнирных платформ.\n\n> 1.2 Все голосовые и текстовые каналы ивента, а также текстовый и голосовой чат игры модерируются Ведущим. Запрещено кидать в мут Ведущего (личный мут) проводящего ивент. Добавление в голосовой канал музыкального бота разрешено только при согласии всех участников ивента.\n\n> 1.3 При старте ивента вы получите информацию о присоединении. Если игрок не заходит в лобби ивента в течение 5 минут (проблемы с интернетом, устанавливается обновление клиента или другая техническая причина, зависящая только от игрока), он дисквалифицируется с ивента.\n\n> 1.4 Запрещено любое препятствие игре или общению, а также переманивание людей с другого клоуза/ивента. Запрещено покидать ивент с момента начала игры, а также переход на другие клоузы/ивенты. Запрещен преднамеренный разрыв соединения. Участники ивента должны хотя бы минимально доносить инфу союзникам."

        embed2 = disnake.Embed()
        embed2.color = 0x2f3136
        embed2.set_author(name="Система назаний за нарушение")
        embed2.description = " На ивенте действует система 3-х предупреждений, по накоплению которых вам будет выдан ивент-бан. В зависимости от степени нарушения время ивент-бан может варьироваться.\n\n> Предупреждение выдается за нарушение правил сервера и правил ивента. В зависимости от степени нарушение правил вам может будет дано устное замечание. При повторном нарушении вам будет выдано предупреждение. При грубом нарушении правил ивент-бан будет выдан без 3-х предупреждений.\n\n> На ивенте не работают серверные репорты. Если вы заметили неадекватное поведение или превышение своих полномочий с стороны Ведущего (и имеете весомые доказательства) вы можете подать жалобу, написав Секьюрити или Куратору (отвечаю за Eventmaker). Все жалобы должны иметь доказательную базу. В частности, нужно использовать скриншоты или откат. Наказания за нарушения выдаются Ведущим в рамках ивента.\n\n> Ивент-бан это блокировка на ивенте, а также ивент-бан может быть обжалован. Для его обжалования свяжитесь с Секьюрити или Куратором (отвечаю за Eventmaker)."

        await interaction.send(embeds=[embed, embed2], ephemeral=True)


class Accept(disnake.ui.View):
    def __init__(self, client, inter, voice_event_channel):
        super().__init__()
        self.client = client

        self.inter = inter
        self.voice_event_channel = voice_event_channel

        url = f"{voice_event_channel.jump_url}"

        view = disnake.ui.View(timeout=None)
        view.add_item(disnake.ui.Button(
            label="Присоединиться к ивенту", url=url))


class Dropdown(disnake.ui.Select):
    def __init__(self, client, inter):
        self.client = client
        emo2 = 1143636018373853275
        global money
        money = self.client.get_emoji(emo2)
        self.inter = inter

        options = [
            disnake.SelectOption(
                label="Шляпа"
            ),
            disnake.SelectOption(
                label="Коднеймс"
            ),
            disnake.SelectOption(
                label="Кто я"
            ),
            disnake.SelectOption(
                label="Своя Игра/Si Game"
            ),
            disnake.SelectOption(
                label="Монополия"
            ),
            disnake.SelectOption(
                label="Бункер"
            ),
            disnake.SelectOption(
                label="Gartic Phone"
            ),
            disnake.SelectOption(
                label="Дурак онлайн"
            ),
            disnake.SelectOption(
                label="Jackbox"
            ),
            disnake.SelectOption(
                label="Крокодил"
            )
        ]

        super().__init__(
            placeholder="Выберите ивент",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        global event_name
        global is_event
        try:
            if is_event[interaction.author.id]:
                embed = disnake.Embed()
                embed.description = f"> Вы не можете создать больше 1 ивента!"
                embed.color = 0x2f3136
                await interaction.send(embed=embed, ephemeral=True)
                return
        except KeyError:
            pass
        is_event.update({interaction.author.id: True})
        if self.values[0] == 'Шляпа':
             gif = 'https://i.imgur.com/3V7jGzz.gif'

        if self.values[0] == 'Коднеймс':
             gif = 'https://i.imgur.com/wnZRpKD.gif'

        if self.values[0] == 'Кто я':
             gif = 'https://media.discordapp.net/attachments/1048616209739944006/1101515547906154596/2a898eb5a7fa372a.png?width=1439&height=647'

        if self.values[0] == 'Своя Игра/Si Game':
             gif = 'https://cdn.discordapp.com/attachments/1077576210512609402/1087014563842621510/ezgif-3-85e86c0fc7.gif'

        if self.values[0] == 'Монополия':
             gif = 'https://i.imgur.com/ehWi5Zv.gif'

        if self.values[0] == 'Бункер':
             gif = 'https://i.imgur.com/C11C4We.gif'

        if self.values[0] == 'Gartic Phone':
             gif = 'https://cdn.discordapp.com/attachments/1048616209739944006/1101515546727567370/39c73592073f5313.png'

        if self.values[0] == 'Дурак онлайн':
             gif = 'https://cdn.discordapp.com/attachments/1077576210512609402/1087014566422138890/ezgif-3-88bc87955c.gif'

        if self.values[0] == 'Jackbox':
             gif = 'https://cdn.discordapp.com/attachments/1077576210512609402/1087014565792972911/ezgif-3-0fad24ed74.gif'

        if self.values[0] == 'Крокодил':
             gif = 'https://media.discordapp.net/attachments/1048616209739944006/1101515547906154596/2a898eb5a7fa372a.png?width=1439&height=647'

        await interaction.response.defer()
        try:
            await interaction.user.edit(nick='!Ведущий')
        except disnake.Forbidden:

            embed = disnake.Embed()
            embed.description = f"> У бота не хватает прав вам изменить ник. Пожалуйста, измените ник на ``!Ведущий``"
            embed.color = 0x2f3136
            await interaction.user.send(embed=embed)

        category = await interaction.guild.create_category(name=f'🟢{self.values[0]}・{interaction.author}', position=disnake.utils.get(interaction.guild.categories, id=int(events['categories_creat_id'])).position)
        await category.set_permissions(disnake.utils.get(interaction.guild.roles, id=int(events['ban_id_role'])), view_channel=False)
        await category.set_permissions(disnake.utils.get(interaction.guild.roles, id=int(events['new_member'])), view_channel=False)
        await category.set_permissions(disnake.utils.get(interaction.guild.roles, id=int(events['local_ban_role'])), view_channel=False)
        event = await interaction.author.guild.create_voice_channel(f'🎲・{self.values[0]}', category=category)
        uprav = await interaction.author.guild.create_text_channel(f'📢・управление', category=category)
        info = await interaction.author.guild.create_text_channel(f'📑・Информация', category=category)
        chat = await interaction.author.guild.create_text_channel(f'💬・чат', category=category)
        await uprav.set_permissions(interaction.guild.default_role, send_messages=True, read_message_history=False, read_messages=False)
        await uprav.set_permissions(interaction.author, send_messages=True, read_message_history=True, read_messages=True)
        await info.set_permissions(interaction.guild.default_role, send_messages=False)
        await event.set_permissions(interaction.author, mute_members=True)
        await chat.set_permissions(interaction.author, view_channel=True, send_messages=True, read_message_history=True, read_messages=True)
        await info.set_permissions(disnake.utils.get(interaction.guild.roles, id=int(events['male_role'])), send_messages=False)
        await info.set_permissions(disnake.utils.get(interaction.guild.roles, id=int(events['boy_role'])), send_messages=False)
        await info.set_permissions(disnake.utils.get(interaction.guild.roles, id=int(events['event_maker_role'])), send_messages=True)
        offset = datetime.timezone(datetime.timedelta(hours=3))
        time = datetime.datetime.now(offset)
        time = time.strftime(r"%H:%M")

        text_event_channel = uprav
        voice_event_channel = disnake.utils.get(
            interaction.author.guild.voice_channels, name=f'🎲・{self.values[0]}')

        if await staff.find_one({"id": interaction.author.id}) is None:
            await staff.insert_one({
                "id": interaction.author.id,
                "online": 0,
                "warns": 0,
                "events": 1,
                "bans": 0,
                "fols": 0,
                "week_online": 0,
                "week_events": 0,
                "week_bans": 0,
                "week_fols": 0
            })
        else:
            await staff.update_one({"id": interaction.author.id}, {"$inc": {"week_events": 1}})
            await staff.update_one({"id": interaction.author.id}, {"$inc": {"events": 1}})

        await eventvoice.insert_one({"voice": voice_event_channel.id, "leader": interaction.author.id})

        logieve = self.client.get_channel(int(events['log_event_chanel']))
        embed_ = disnake.Embed(
            title="Логи — Ивентов", color=0x2F3136)
        event_name = self.values[0]

        embed_.add_field(
            name="Ивент", value=f"```{event_name}```")
        embed_.add_field(
            name="Ведущий", value=f"```{interaction.author}```")
        embed_.add_field(
            name="Ивент начался", value=f'```{datetime.datetime.now().strftime(r"%H:%M")}```')
        embed_.description = f'В **{time}** начнется **ивент** {event_name}.\nВедущий - {interaction.author.mention}'

        view = disnake.ui.View(timeout=None)
        view.add_item(disnake.ui.Button(
            label="Присоединиться к ивенту", url=voice_event_channel.jump_url))
        global dot
        dot = self.client.get_emoji(1143829698279919666)
        if self.values[0] == 'Шляпа':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'Ивент {self.values[0]}', description=f'```Шляпа — командно-индивидуальная или парная интеллектуальная игра, в которой игрок должен за небольшое время объяснить как можно больше слов, чтобы его партнер их отгадал. Англоязычный аналог этой игры — «Alias».```', color=0x2f3136)
            embed.set_image(url="https://i.imgur.com/3V7jGzz.gif")
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```150```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)

            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Alias | Шляпа ・ GitHub Fequme**\n{dot} **Описание игры:**\n```За основу игры взяты Шляпа и Alias. Можно играть парами, можно командами. Объясняющий меняется каждый ход, за минуту необходимо объяснить как можно больше слов, каждое отгаданное слово даёт один балл команде. В конце каждого раунда игроки вручную выставляют баллы по каждому слову, так что правила засчитывания слов могут быть произвольными.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.\n{dot} Использование SoundPad и прочих программ.\n{dot} Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Намеренно руинить игру.\n{dot}  Объясняющему запрещено произносить слова, однокоренные загаданному слову.\n{dot}  Объясняющему запрещено произносить аббревиатуры, одна из букв которых обозначает загаданное слово.\n{dot} Объясняющему запрещено произносить слова, созвучные загаданному слову.\n{dot} Объясняющему запрещено произносить слова, не существующие в русском языке.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://i.imgur.com/3V7jGzz.gif")
            await info.send(embed=embed, view=Rules())
    

        if self.values[0] == 'Коднеймс':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```Командно-индивидуальная или парная интеллектуальная игра, в которой игрок должен за небольшое время объяснить как можно больше слов, чтобы его партнер их отгадал.```', color=0x2f3136)
            embed.set_image(url="https://i.imgur.com/wnZRpKD.gif")
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```150```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Codenames・ GitHub Fequme**\n{dot} **Описание игры:**\n```Игроки делятся на две команды, равные по силе и количеству. Для стандартной игры потребуется минимум четыре человека. Каждая команда выбирает себе капитана. Капитаны знают 25 карточек. Игроки же знают их только по их кодовым словам. Капитаны по очереди дают подсказки, состоящие из одного слова. Слово может относиться к нескольким карточкам, выложенным на столе. Игроки пытаются отгадать кодовые имена, которые имеет в виду их капитан. Если это слово, относящийся к их команде, игроки продолжают отгадывать, пока не ошибутся и не израсходуют свои попытки. Команда, которой первой удалось найти все свои слова, выигрывает.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot} Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Общение между командой и капитаном.\n{dot}  Переговариваться не в свой ход.\n{dot}  Намеренно руинить игру.\n{dot} Сливать информацию.\n{dot} Использовать части в шифре.\n{dot}{dot} Использовать больше одного слова для подсказок.\n{dot}{dot}Если капитан команды дал шифр с нарушением правил, ход сразу же переходит к другой команде.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://i.imgur.com/wnZRpKD.gif")
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Кто я':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```В этой игре ты можешь проявить свою оригинальность, загадывая другим людям забавные (или не очень) слова. Кто я? Птица или самолёт? А может просто сущность?...```', color=0x2f3136)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519074904772749/f06349eef716a929.png?width=1439&height=647")
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```200```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Кто я・ GitHub Fequme**\n{dot} **Описание игры:**\n```Один из игроков становится ведущим (каждый раунд новый), а остальные игроки получают слово, на которое нужно намекнуть ведущему словом-подсказкой. \nКак только все отправят свои подсказки, начинается этап удаления дубликатов: все слова, имеющие одинаковые корни, должны быть удалены игроками, ведущий их не увидит — так что не стоит писать слишком очевидную ассоцицию, велика вероятность, что её напишет кто-то ещё. Так же в этот этап следует удалить слова, нарушающие правила.\nДалее ведущий, видя оставшиеся подсказки, должен угадать оригинальное слово. В случае успеха, он должен поставить «сердечко» самой полезной подсказке, или просто самой понравившейся.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot} Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Намеренно руинить игру.\n{dot}  Объясняющим запрещено писать слова, однокоренные загаданному слову.\n{dot}  Объясняющим запрещено писать аббревиатуры, одна из букв которых обозначает загаданное слово.\n{dot} Объясняющим запрещено писать слова, созвучные загаданному слову.\n{dot} Объясняющим запрещено писать слова, не существующие в русском языке.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519074904772749/f06349eef716a929.png?width=1439&height=647")
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Своя Игра/Si Game':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```«SIGame» — увлекательная интеллектуальная игра. Вы можете проверить собственные знания в различных областях.Основной процесс в игре — ответ на вопросы. Вопросы в игре сформулированы, как правило, в виде утверждений, где искомое слово заменено местоимением.```', color=0x2f3136)
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```300```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Своя Игра/Si Game・ GitHub Fequme**\n{dot} **Описание игры:**\n```Игра проводится между командой.. Обычно в команде играет не более 6 человек. Одновременно играют все участники. Участникам предлагается несколько тем (обычно 8-12), разбитых поровну на два раунда – «Синий» и «Красный». Каждая тема состоит из 5 вопросов разной степени сложности, в Синем раунде – от 10 до 50 баллов, в Красном раунде – от 20 до 100. 10 баллов «стоит» самый простой вопрос темы, 50 — самый трудный.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot} Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Намеренно руинить игру.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Монополия':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```Это игра для тех, кто всегда мечтал стать успешным предпринимателем. Зарабатывай миллионы, собирай монополии, продавай и покупай.```', color=0x2f3136)
            embed.set_image(url="https://i.imgur.com/ehWi5Zv.gif")
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money} Награда за победу:", value=f"```300```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Монополия・ GitHub Fequme**\n{dot} **Описание игры:**\n```Игроки поочередно бросают кубики и делают соответствующее количество ходов на игральном поле. Встав на поле с фирмой, игрок может приобрести её, если фирма свободна; а если фирма принадлежит другому игроку, то игрок обязан заплатить за посещение данного поля аренду по установленному правилами прейскуранту . При посещении поля с событиями игрок получает указание следовать выпавшему ему событию. Игрок может обменивать свои поля на чужие у других игроков, при этом, конечно, получатель предложения может отказаться от вашей сделки. Помните, выгодная сделка увеличивает ваш шанс на победу.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot}  Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n <:5_:930153466456838174> Употребление нецензурной брани.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://i.imgur.com/ehWi5Zv.gif")
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Бункер':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```Бункер - На нашу планету обрушилась глобальная катастрофа. Вы – один из выживших, которых осталось совсем немного. Ваша личная задача – любой ценой попасть в бункер, ведь такой шанс получат далеко не все.```', color=0x2f3136)
            embed.set_image(url="https://i.imgur.com/C11C4We.gif")
            embed.add_field(
                name="<:d6069dd748b08867:1101530092791922728>Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name="<:d6069dd748b08867:1101530092791922728>Награда за победу:", value=f"```300```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://i.imgur.com/C11C4We.gif")
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Бункер・ GitHub Fequme**\n{dot} **Описание игры:**\n```Игроки — это немногие выжившие после обрушившейся на планету катастрофы. Цель каждого из них — попасть в бункер, ведь там места хватит только для половины. Команда, в свою очередь, должна следить, чтобы в укрытии оказался только здоровый генофонд. Каждый участник получает характеристику — профессию, состояние здоровья, биологические параметры, хобби, фобии, навыки, личные качества. На основании описания другие игроки принимают решение, достоин ли кандидат оказаться в убежище.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot}  Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Намеренно руинить игру.\n{dot}  Переходить на личность .\n{dot}  Использовать опыт из реальной жизни.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://i.imgur.com/C11C4We.gif")
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Gartic Phone':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```Gartic Phone - Каждый игрок должен написать необычное или остроумное предложение. Ты получишь странное предложение и должен нарисовать то, что в нем написанно. Попробуй описать полученный безумный рисунок. Посмотри на смешные результаты игры в испорченный телефон.```', color=0x2f3136)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519072048455801/cd305c4117b21108.png?width=1439&height=647")
            embed.add_field(
                name=f"{money} Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```300```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519072048455801/cd305c4117b21108.png?width=1439&height=647")
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Gartic Phone・ GitHub Fequme**\n{dot} **Описание игры:**\n```Сначала каждый пишет смешную фразу. Следующий участник должен нарисовать действие, которое указано в предложении, а ты постарайся изобразить то, что накалякал другой геймер. Третий ход опять передает сообщение соседу, старающемуся пересказать смысл картинки.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot} Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Намеренно руинить игру.\n{dot}  Рисовать буквы/символы/цифры.\n{dot}  Подсказывать игрокам которые еще не отгадали.\n{dot} Рисовать шок-контент.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519072048455801/cd305c4117b21108.png?width=1439&height=647")
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Дурак онлайн':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```Самая популярная карточная игра. Благодаря простым правилам в неё любят играть и взрослые, и дети. Первым ходом кидайте любую карту. Кроющийся должен покрыть каждую подкинутую под него карту картой той же масти, но большего достоинства, или любым козырем. Козырную карту можно покрыть только козырем большего достоинства. Козырная масть определяется картой под колодой. Подкидывать можно карты того же достоинства, что и карты лежащие на столе. Если кроющийся всё покрыл, а подкидывать больше нечего (или не хочется), жмите «Бито». Если вам нечем крыться (или не хочется), жмите «Беру». Подкидывать можно не больше 6 карт, или не больше, чем есть карт у кроющегося. Если кроющийся отбился, то следующий первый ход за ним. Если же взял, то будет ходить следующий по часовой стрелке игрок. Проигрывает игрок, последним оставшийся с картами на руках. ```', color=0x2f3136)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519073130590341/bae19e9879cf87bb.png?width=1439&height=647")
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```300```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519073130590341/bae19e9879cf87bb.png?width=1439&height=647")
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Дурак онлайн・GitHub Fequme**\n{dot} **Описание игры:**\n```Самая популярная карточная игра. Благодаря простым правилам в неё любят играть и взрослые, и дети. Первым ходом кидайте любую карту. Кроющийся должен покрыть каждую подкинутую под него карту картой той же масти, но большего достоинства, или любым козырем. Козырную карту можно покрыть только козырем большего достоинства. Козырная масть определяется картой под колодой. Подкидывать можно карты того же достоинства, что и карты лежащие на столе. Если кроющийся всё покрыл, а подкидывать больше нечего (или не хочется), жмите «Бито». Если вам нечем крыться (или не хочется), жмите «Беру». Подкидывать можно не больше 6 карт, или не больше, чем есть карт у кроющегося. Если кроющийся отбился, то следующий первый ход за ним. Если же взял, то будет ходить следующий по часовой стрелке игрок. Проигрывает игрок, последним оставшийся с картами на руках. ```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot} Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Намеренно руинить игру.\n{dot}  Использовать подсказки без разрешения ведущего.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519073130590341/bae19e9879cf87bb.png?width=1439&height=647")
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Jackbox':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```Виртуальная коробка, полная веселья! Играть в неё можно с любого современного браузера на смартфоне, планшете или компьютере. Она содержит в себе несколько довольно интересных игр, которые отлично подходят для того, чтобы провести время в приятной компании.```', color=0x2f3136)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519072602099825/d815f53f65d7cd23.png?width=1439&height=647")
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```75```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```200```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519072602099825/d815f53f65d7cd23.png?width=1439&height=647")
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Jackbox・GitHub Fequme**\n{dot} **Описание игры:**\n```Виртуальная коробка, полная веселья! Играть в неё можно с любого современного браузера на смартфоне, планшете или компьютере. Она содержит в себе несколько довольно интересных игр, которые отлично подходят для того, чтобы провести время в приятной компании. ```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot}  Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot}> Общение участников при объяснении правил или при какой либо речи со стороны игры.\n{dot}  Разглать доступную вам информацию недоступную другим игрокам.\n{dot}  Намеренно руинить игру.\n{dot}  Заходить в не начавшуюся игру с разных устройств при наличии активных вариантов игры.\n{dot} Использование слов/выражений не существующих в русском языке если этого не требует сама игра.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519072602099825/d815f53f65d7cd23.png?width=1439&height=647")
            await info.send(embed=embed, view=Rules())

        if self.values[0] == 'Крокодил':
            anons_channel = disnake.utils.get(
                interaction.author.guild.text_channels, id=int(events['anons_channel']))
            embed = disnake.Embed(
                title=f'{dot} Ивент {self.values[0]}', description=f'```Если ты хочешь показать всем свои творческие способности, то этот ивент для тебя! На нём ты будешь рисовать и отгадывать слова, получая за это награды.```', color=0x2f3136)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519074325962792/c05a67a1c736572c.png?width=1439&height=647")
            embed.add_field(
                name=f"{money}  Награда за участие: ", value=f"```100```", inline=True)
            embed.add_field(
                name=f"{money}  Награда за победу:", value=f"```300```", inline=True)

            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519074325962792/c05a67a1c736572c.png?width=1439&height=647")
            msg = await anons_channel.send(f"<@&{(events['ping_role'])}>", embed=embed, view=view)

            embed = disnake.Embed(
                description=f"**{dot} Крокодил・GitHub Fequme**\n{dot} **Описание игры:**\n```Рисуйте и выигрывайте. Угадывайте, что рисуют другие, и тоже выигрывайте! Здесь все также, только загадывать слова, а вернее, давать несколько на выбор, вам будет сама игра. Если вы – ведущий, вы должны будете выбрать максимально простое и понятное для вас слово и попытаться его нарисовать на игровом экране. Остальные участники должны угадать, что вы пытаетесь изобразить. Если никто не угадал, ваши попытки провалились, и вы проиграли. Вот это все, что нужно знать об игре. Несмотря на простоту правил, развлечение точно нельзя назвать скучным, время пройдет незаметно, а развязка порой бывает очень неожиданно.```\n\n{dot} **Запрещается:**\n\n{dot}  Создавать помеху проведению мероприятия.D\n{dot} Использование SoundPad и прочих программ.\n{dot} Провоцировать участников на конфликт.\n{dot}Оскорблять игроков и ведущего мероприятия.\n{dot}  Употребление нецензурной брани.\n{dot} Намеренно руинить игру.\n{dot}  Рисовать буквы/символы/цифры.\n{dot}  Подсказывать игрокам которые еще не отгадали.\n{dot}  Рисовать шок-контент.", color=0x2f3136)
            embed.set_footer(
                text=f'・Ведущий: {interaction.author}', icon_url=interaction.author.display_avatar)
            embed.set_image(url="https://media.discordapp.net/attachments/1048616209739944006/1101519074325962792/c05a67a1c736572c.png?width=1439&height=647")
            await info.send(embed=embed, view=Rules())

        embed3 = disnake.Embed(
            title=f'Ивент {self.values[0]}', description=f'Вы успешно создали ивент **{self.values[0]}**, начало в **{time}**', color=0x2f3136)
        embed3.set_thumbnail(url=interaction.author.display_avatar)
        await interaction.edit_original_message(embed=embed3, view=None)

        embed3 = disnake.Embed(title=f'Управление Ивентом: {interaction.author.name}',
                               description=f'**Ивент:** {self.values[0]}\n**Начало ивента:** {time}\n**Голосовой канал:** {voice_event_channel.mention}\n**Текстовой канал:** {chat.mention}', color=0x2f3136)
        embed3.set_thumbnail(url=interaction.author.display_avatar)
        message_log = await logieve.send(embed=embed_)
        await text_event_channel.send(embed=embed3, view=ManageEvent(self.client, self.inter, uprav, event, info, chat, category, message_log, datetime.datetime.now(), view, msg))


class DropdownView(disnake.ui.View):
    def __init__(self, client, inter):
        super().__init__()
        self.client = client
        self.inter = inter

        self.add_item(Dropdown(self.client, self.inter))


class EventMaker(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener("on_voice_state_update")
    async def viewers(self, member: disnake.Member, _: disnake.VoiceState, after: disnake.VoiceState):
        if not after or not after.channel:
            return
        if not await eventvoice.find_one({"voice": after.channel.id}):
            return
        await eventvoice.update_one({"voice": after.channel.id}, {"$push": {"viewers": member.id}})

    @tasks.loop(seconds=60)
    async def test(self):
        await self.client.wait_until_ready()
        for guild in self.client.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if await eventvoice.find_one({"leader": member.id}) is not None:
                        if await staff.find_one({"id": member.id}) is None:
                            await staff.insert_one({
                                "id": member.id,
                                "online": 60,
                                "warns": 0,
                                "events": 0,
                                "bans": 0,
                                "fols": 0,
                                "week_online": 0,
                                "week_events": 0,
                                "week_bans": 0,
                                "week_fols": 0
                            })
                        else:
                            await staff.update_one({"id": member.id}, {"$inc": {"online": 60}})
                            await staff.update_one({"id": member.id}, {"$inc": {"week_online": 60}})

    @commands.Cog.listener("on_voice_state_update")
    async def voice_state(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        after_channel_id = after.channel.id if after.channel else None
        before_channel_id = before.channel.id if before.channel else None
        if after_channel_id == before_channel_id:
            return
        query1 = await eventvoice.find_one({"voice": before_channel_id})
        query2 = await eventvoice.find_one({"voice": after_channel_id})
        if not query1 and not query2:
            return
        query = query1 or query2
        if after_channel_id != query['voice'] and before_channel_id in [query['voice'], None]:
            try:
                await member.edit(mute=False, deafen=False)
            except disnake.HTTPException:
                pass
            if not member.voice:
                def check(member_voice: disnake.Member, _: disnake.VoiceState,
                          after_voice: disnake.VoiceState):
                    if not after_voice.channel:
                        return False
                    return member_voice == member and after_voice.channel \
                        and after_voice.channel.id != query['voice']

                await self.client.wait_for('voice_state_update', check=check)
                await member.edit(mute=False, deafen=False)

    @commands.slash_command(name="event")
    @commands.has_any_role(int(events['event_maker_role']))
    async def event(self, inter):
        pass

    @event.sub_command(name='create', description='Создать ивент')
    @commands.has_any_role(int(events['event_maker_role']))
    async def make(self, inter):
        global is_event
        try:
            if is_event[inter.author.id]:
                embed = disnake.Embed()
                embed.description = f"> Вы не можете создать больше 1 ивента!"
                embed.color = 0x2f3136
                await inter.send(embed=embed, ephemeral=True)
                return
        except KeyError:
            pass
        embed = disnake.Embed(
            title='Создать ивент', description='Выберите ивент который хотели бы провести!', color=0x2f3136)
        embed.set_thumbnail(url=inter.author.display_avatar)
        embed.timestamp = datetime.datetime.now()

        await inter.send(embed=embed, view=DropdownView(self.client, inter), ephemeral=True)

    @event.sub_command(name="stats", description="Статистика ивентера")
    async def statsfff(self, inter, member: disnake.Member = None):
        role = disnake.utils.get(
            inter.guild.roles, id=int(events['event_maker_role']))
        if member is None:
            if role in inter.author.roles:
                if await staff.find_one({"id": inter.author.id}) is not None:
                    docs = await staff.find_one({"id": inter.author.id})
                    embed = disnake.Embed()
                    embed.color = 0x2f3136
                    embed.set_author(name=f"Статистика - {inter.author}")
                    embed.description = f"> ID: {inter.author.id}"
                    embed.add_field(
                        name="Онлайн", value=f"```\n{convert_time(docs['online'])}```", inline=True)
                    embed.add_field(
                        name="Предупреждения", value=f"```{docs['warns']} / 3```", inline=True)
                    embed.add_field(name="Количество проведенных ивентов",
                                    value=f"```{docs['events']}```", inline=True)
                    embed.add_field(name="Количество выданных блокировок",
                                    value=f"```\n{docs['bans']}```", inline=True)
                    embed.add_field(
                        name="Количество выданных фолов", value=f"```\n{docs['fols']}```", inline=True)

                    await inter.send(embed=embed, view=Weekd(mem=inter.author), ephemeral=True)
                else:
                    await staff.insert_one({
                        "id": inter.author.id,
                        "online": 0,
                        "warns": 0,
                        "events": 0,
                        "bans": 0,
                        "fols": 0,
                        "week_online": 0,
                        "week_events": 0,
                        "week_bans": 0,
                        "week_fols": 0
                    })

                    docs = await staff.find_one({"id": inter.author.id})
                    embed = disnake.Embed()
                    embed.set_author(name=f"Статистика - {inter.author}")
                    embed.color = 0x2f3136
                    embed.description = f"> ID: {inter.author.id}"
                    embed.add_field(
                        name="Онлайн", value=f"```\n{convert_time(docs['online'])}```", inline=True)
                    embed.add_field(
                        name="Предупреждения", value=f"```{docs['warns']} / 3```", inline=True)
                    embed.add_field(name="Количество проведенных ивентов",
                                    value=f"```{docs['events']}```", inline=True)
                    embed.add_field(name="Количество выданных блокировок",
                                    value=f"```\n{docs['bans']}```", inline=True)
                    embed.add_field(
                        name="Количество выданных фолов", value=f"```\n{docs['fols']}```", inline=True)

                    await inter.send(embed=embed, view=Weekd(mem=inter.author), ephemeral=True)
            else:
                embed = disnake.Embed()
                embed.color = 0x2f3136
                embed.description = "> Вы не можете просмотреть статистику для ивентов, поскольку вы не являетесь ивентером."
                await inter.send(embed=embed, ephemeral=True)
        else:
            if role in member.roles:
                if await staff.find_one({"id": member.id}) is not None:
                    docs = await staff.find_one({"id": member.id})
                    embed = disnake.Embed()
                    embed.set_author(name=f"Статистика - {member}")
                    embed.description = f"> ID: {member.id}"
                    embed.color = 0x2f3136
                    embed.add_field(
                        name="Онлайн", value=f"```\n{convert_time(docs['online'])}```", inline=True)
                    embed.add_field(
                        name="Предупреждения", value=f"```{docs['warns']} / 3```", inline=True)
                    embed.add_field(name="Количество проведенных ивентов",
                                    value=f"```{docs['events']}```", inline=True)
                    embed.add_field(name="Количество выданных блокировок",
                                    value=f"```\n{docs['bans']}```", inline=True)
                    embed.add_field(
                        name="Количество выданных фолов", value=f"```\n{docs['fols']}```", inline=True)

                    await inter.send(embed=embed, view=Weekd(mem=member), ephemeral=True)
                else:
                    await staff.insert_one({
                        "id": member.id,
                        "online": 0,
                        "warns": 0,
                        "events": 0,
                        "bans": 0,
                        "fols": 0,
                        "week_online": 0,
                        "week_events": 0,
                        "week_bans": 0,
                        "week_fols": 0
                    })

                    docs = await staff.find_one({"id": member.id})
                    embed = disnake.Embed()
                    embed.set_author(name=f"Статистика - {member}")
                    embed.description = f"> ID: {member.id}"
                    embed.color = 0x2f3136
                    embed.add_field(
                        name="Онлайн", value=f"```\n{convert_time(docs['online'])}```", inline=True)
                    embed.add_field(
                        name="Предупреждения", value=f"```{docs['warns']} / 3```", inline=True)
                    embed.add_field(name="Количество проведенных ивентов",
                                    value=f"```{docs['events']}```", inline=True)
                    embed.add_field(name="Количество выданных блокировок",
                                    value=f"```\n{docs['bans']}```", inline=True)
                    embed.add_field(
                        name="Количество выданных фолов", value=f"```\n{docs['fols']}```", inline=True)

                    await inter.send(embed=embed, view=Weekd(mem=member), ephemeral=True)
            else:
                embed = disnake.Embed()
                embed.color = 0x2f3136
                embed.description = "> Пользователь, не является ивентером."
                await inter.send(embed=embed, ephemeral=True)

    @event.sub_command(name="top", description="Топ ивентеров")
    async def leaderboard(self, inter):
        role = disnake.utils.get(
            inter.guild.roles, id=int(events['event_maker_role']))
        if role in inter.author.roles:
            await inter.response.defer(ephemeral=True)
            em = {
                1: "1. ",
                2: "2. ",
                3: "3. ",
                4: "4. ",
                5: "5. ",
                6: "6. ",
                7: "7. ",
                8: "8. ",
                9: "9. ",
                10: "10. "
            }

            iters = 10
            # staff.find(limit=iters).sort("events", -1)
            # count = 0
            text = ""
            # try:
            top_list = [doc async for doc in staff.find(limit=iters).sort("events", -1)]
            if not top_list:
                embed = disnake.Embed()
                embed.title = "Доска лидеров по проведению ивентов"
                embed.description = "Данная доска **пуста**!"
                embed.set_thumbnail(url=inter.author.display_avatar)
                embed.color = 0x2f3136
                return await inter.send(embed=embed, ephemeral=True)

            for place, x in enumerate(top_list, start=1):
                nam = inter.guild.get_member(
                    int(x["id"])
                )

                if nam == None:
                    continue

                lvl = x["events"]
                if lvl == 0:
                    continue
                # else:
                    # count += 1
                text += f"{em[place]} {nam.mention} - проведено **{lvl}** ивентов\n"

            embed = disnake.Embed()
            embed.title = "Доска лидеров по проведению ивентов"
            embed.description = f"{text}"
            embed.color = 0x2f3136
            embed.set_thumbnail(url=inter.author.display_avatar)

            await inter.send(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed()
            embed.description = f"> Для просмотра статистики вам нужно быть ивентером!"
            embed.color = 0x2f3136

            await inter.send(embed=embed, ephemeral=True)

    @event.sub_command(name="warn", description="выдать варн")
    async def warn(self, inter, member: disnake.Member, reason: str):
        role = disnake.utils.get(inter.guild.roles, id=int(
            events['admin_for_eventmaker']))
        role2 = disnake.utils.get(
            inter.guild.roles, id=int(events['event_maker_role']))

        if not member.bot:
            if role in inter.author.roles:
                if not member == inter.author:
                    if role2 in member.roles:
                        if await staff.find_one({"id": member.id}) is None:
                            await staff.insert_one({
                                "id": member.id,
                                "online": 0,
                                "warns": 1,
                                "events": 0,
                                "bans": 0,
                                "fols": 0,
                                "week_online": 0,
                                "week_events": 0,
                                "week_bans": 0,
                                "week_fols": 0
                            })

                            embed = disnake.Embed()
                            embed.description = f"> Вы успешно выдали предупреждение пользователю {member.mention}"
                            embed.color = 0x2f3136
                            await inter.response.send_message(embed=embed, ephemeral=True)
                        else:
                            docs = await staff.find_one({"id": member.id})
                            warns = docs['warns']
                            if warns >= 2:
                                await staff.update_one({"id": member.id}, {"$set": {"warns": 0}})
                                if await staffwarns.find_one({"id": member.id}) is not None:
                                    await staffwarns.delete_many({"id": member.id})
                                try:
                                    await member.remove_roles(role2)
                                except:
                                    pass

                                embed = disnake.Embed()
                                embed.description = f"> Пользователь {member.mention} был снят с должности ивентера, поскольку достиг 3-х предупреждений"
                                embed.color = 0x2f3136
                                await inter.response.send_message(embed=embed, ephemeral=True)
                            else:
                                date = (datetime.datetime.now() +
                                        datetime.timedelta(seconds=int(events['time_delete_warn'])))
                                await staffwarns.insert_one({"id": member.id, "date_expired": date})
                                await staff.update_one({"id": member.id}, {"$inc": {"warns": 1}})
                                embed = disnake.Embed()
                                embed.description = f"> Вы успешно выдали предупреждение пользователю {member.mention} по причине: ** {reason} **"
                                embed.color = 0x2f3136
                                await inter.response.send_message(embed=embed, ephemeral=True)

                    else:
                        embed = disnake.Embed()
                        embed.description = f"> Вы не можете выдать пользователю который не является ивентером."
                        embed.color = 0x2f3136
                        await inter.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed()
                embed.description = f"> Вы не можете выдавать предупреждения."
                embed.color = 0x2f3136
                await inter.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed()
            embed.description = f"> Вы не можете взаимодействовать с ботом!"
            embed.color = 0x2f3136
            await inter.response.send_message(embed=embed, ephemeral=True)

    @event.sub_command(name="unwarn", description="снять варн")
    async def unwarnnnn(self, inter, member: disnake.Member = None):
        role = disnake.utils.get(inter.guild.roles, id=int(
            events['admin_for_eventmaker']))
        role2 = disnake.utils.get(
            inter.guild.roles, id=int(events['event_maker_role']))

        if not member == inter.author:
            if not member.bot:
                if role in inter.author.roles:
                    if role2 in member.roles:
                        if await staff.find_one({"id": member.id}):
                            docs = await staff.find_one({"id": member.id})
                            warns = docs['warns']
                            if not warns <= 0:
                                await staff.update_one({"id": member.id}, {"$inc": {"warns": -1}})
                                embed = disnake.Embed()
                                embed.description = f"> Пользователю {member.mention} был снят выговор!"
                                embed.color = 0x2f3136
                                await inter.response.send_message(embed=embed, ephemeral=True)
                            else:
                                embed = disnake.Embed()
                                embed.description = f"> Пользователь {member.mention} не имеет выговоров!"
                                embed.color = 0x2f3136
                                await inter.response.send_message(embed=embed, ephemeral=True)
                        else:
                            await staff.insert_one({
                                "id": member.id,
                                "online": 0,
                                "warns": 0,
                                "events": 0,
                                "bans": 0,
                                "fols": 0,
                                "week_online": 0,
                                "week_events": 0,
                                "week_bans": 0,
                                "week_fols": 0
                            })

                            embed = disnake.Embed()
                            embed.description = f"> Пользователь {member.mention} не имеет выговоров!"
                            embed.color = 0x2f3136
                            await inter.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = disnake.Embed()
                        embed.description = f"> Указанный пользователь не является ивентером"
                        embed.color = 0x2f3136
                        await inter.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed()
                    embed.description = f"> Вы не можете снимать предупреждения!"
                    embed.color = 0x2f3136
                    await inter.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed()
                embed.description = f"> Нельзя взаимодействовать с ботом!"
                embed.color = 0x2f3136
                await inter.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed()
            embed.description = f"> Нельзя снять предупреждение самому себе!"
            embed.color = 0x2f3136
            await inter.response.send_message(embed=embed, ephemeral=True)

    @event.sub_command(description="Выдать ивент бан")
    @commands.has_any_role(int(events['event_maker_role']))
    async def ban(self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member, days: int, reason: str):
        if not member == interaction.author:
            if not member.bot:
                if await staff.find_one({"id": interaction.author.id}) is None:
                    await staff.insert_one({
                        "id": interaction.author.id,
                        "online": 0,
                        "warns": 0,
                        "events": 0,
                        "bans": 1,
                        "fols": 0,
                        "week_online": 0,
                        "week_events": 0,
                        "week_bans": 0,
                        "week_fols": 0
                    })
                else:
                    await staff.update_one({"id": interaction.author.id}, {"$inc": {"week_bans": 1}})
                    await staff.update_one({"id": interaction.author.id}, {"$inc": {"bans": 1}})

                    ev_ban = disnake.utils.get(
                        interaction.guild.roles, id=int(events['ban_id_role']))
                    await member.add_roles(ev_ban, reason=reason)
                    await member.edit(voice_channel=None)
                    date_expired = datetime.datetime.now() + datetime.timedelta(days=days)
                    if await close_bans.find_one({"_id": member.id}) is None:
                        await close_bans.insert_one({"_id": member.id, "close_ban": date_expired})
                    await close_bans.update_one({"_id": member.id}, {"$set": {"close_ban": date_expired}})
                    aembed = disnake.Embed()
                    aembed.description = f"> Вы успешно выдали Event Ban пользователю {member.mention}"
                    aembed.color = 0x2f3136
                    aembed.set_thumbnail(url=interaction.author.display_avatar)
                    emb = disnake.Embed(color=0x2f3136)
                    emb.set_author(name=f'Вам был выдан ивент бан',
                                   icon_url='https://cdn-icons-png.flaticon.com/512/6715/6715772.png')

                    emb.add_field(
                        name="Кто выдал", value=f"```{interaction.author}```")
                    emb.add_field(
                        name="Время", value=f"```{days}days```", inline=True)
                    emb.add_field(
                        name="Причина", value=f"```{reason}```", inline=True)
                    emb.set_thumbnail(
                        url='https://media.discordapp.net/attachments/1077576210512609402/1082451030203170907/ava_3.gif?width=563&height=563?size=4096')
                    try:
                        msg_mem = await member.send(embed=emb)

                    except disnake.Forbidden:
                        pass
                    log_channel = interaction.bot.get_channel(
                        int(events['log_ban_chennel']))
                    emb = disnake.Embed(color=0x2f3136)
                    emb.set_author(name=f'Логи — Ивент банов',
                                   icon_url='https://cdn-icons-png.flaticon.com/512/6715/6715772.png')

                    emb.add_field(
                        name="Кто выдал", value=f"```{interaction.author}```")
                    emb.add_field(
                        name="Кому выдал", value=f"```{member._user}```")
                    emb.add_field(
                        name="Время", value=f"```{days}days```")
                    emb.add_field(
                        name="Причина", value=f"```{reason}```")
                    emb.set_thumbnail(url=interaction.author.display_avatar)
                    await log_channel.send(embed=emb)

            else:
                embed = disnake.Embed()
                embed.description = "> Вы не можете выдать Event Ban **боту**!"
                embed.set_thumbnail(url=interaction.author.display_avatar)
                embed.color = 0x2f3136
                await interaction.send(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed()
            embed.description = "> Вы не можете выдать Event Ban **самому себе**!"
            embed.set_thumbnail(url=interaction.author.display_avatar)
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)

    @event.sub_command(description="Снять ивент бан")
    @commands.has_any_role(int(events['event_maker_role']))
    async def unban(self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        if not member == interaction.author:
            if not member.bot:
                ev_ban = disnake.utils.get(
                    interaction.guild.roles, id=int(events['ban_id_role']))
                await member.remove_roles(ev_ban, reason=reason)
                await close_bans.delete_one({"_id": member.id})

                aembed = disnake.Embed()
                aembed.description = f"> Вы успешно сняли Event Ban пользователю {member.mention}"
                aembed.color = 0x2f3136
                aembed.set_thumbnail(url=interaction.author.display_avatar)
                emb = disnake.Embed(color=0x2f3136)
                emb.set_author(name=f'Вам был снят ивент бан',
                               icon_url='https://cdn-icons-png.flaticon.com/512/6715/6715772.png')

                emb.add_field(
                    name="Кто снял", value=f"```{interaction.author}```")
                emb.add_field(
                    name="Причина снятия", value=f"```{reason}```", inline=True)
                emb.set_thumbnail(url=interaction.author.display_avatar)
                try:
                    msg_mem = await member.send(embed=emb)

                except disnake.Forbidden:
                    pass
                log_channel = interaction.bot.get_channel(
                    int(events['log_ban_chennel']))
                emb = disnake.Embed(color=0x2f3136)
                emb.set_author(name=f'Логи — Ивент банов',
                               icon_url='https://cdn-icons-png.flaticon.com/512/6715/6715772.png')

                emb.add_field(
                    name="Кто снял", value=f"```{interaction.author}```")
                emb.add_field(
                    name="Кому снял", value=f"```{member._user}```")
                emb.add_field(
                    name="Причина снятия", value=f"```{reason}```")
                emb.set_thumbnail(url=interaction.author.display_avatar)
                await log_channel.send(embed=emb)

            else:
                embed = disnake.Embed()
                embed.description = "> Вы не можете снять Event Ban **боту**!"
                embed.set_thumbnail(url=interaction.author.display_avatar)
                embed.color = 0x2f3136
                await interaction.send(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed()
            embed.description = "> Вы не можете снять Event Ban **самому себе**!"
            embed.set_thumbnail(url=interaction.author.display_avatar)
            embed.color = 0x2f3136
            await interaction.send(embed=embed, ephemeral=True)

    @tasks.loop(seconds=604800)
    async def resetstats(self):
        await self.client.wait_until_ready()
        guild = self.client.get_guild(int(events['guild']))
        async for document in staff.find({}):
            try:
                await document.update_one({"id": document["id"]}, {"$set": {"week_online": 0, "week_events": 0, "week_bans": 0, "week_fols": 0}})
            except:
                pass

    @tasks.loop(seconds=60)
    async def checkwarns(self):
        await self.client.wait_until_ready()
        guild = self.client.get_guild(int(events['guild']))
        async for document in staffwarns.find({}):
            try:
                member = await guild.fetch_member(document["id"])
            except disnake.NotFound:
                print("Membet not found")
                continue
            try:
                if document['date_expired'] <= datetime.datetime.now():
                    await staffwarns.delete_one({"id": document["id"]})
                    if await staff.find_one({"id": document["id"]}) is not None:
                        await staff.update_one({"id": document["id"]}, {"$inc": {"warns": -1}})

            except Exception as e:
                print(e)
                print("??? [CHECK-WARNS]")


def setup(client):
    client.add_cog(EventMaker(client))
    print('Cog: "event-create" loaded!')
    print("I started successfully")
