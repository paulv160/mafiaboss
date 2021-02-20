#!/usr/bin/env python
import discord
import logging
import json
import datetime
from pprint import pprint
from discord.ext import commands
from game import Game
from settings import defaultMetadata, defaultRules, defaultRoles
import settings
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open('settings.json') as s:
    settings = json.loads(s.read())
    s.close()


class HelpCommand(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        return f'{self.clean_prefix}{command.qualified_name} {command.signature}{(" - " + str(command.help)).replace(" - None", "")}'

    async def send_bot_help(self, mapping):
        helpEmbed = discord.Embed(title="Mafia Boss Commands")
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [
                self.get_command_signature(c) for c in filtered if c.name not in ('help', 'report')]
            if getattr(cog, "qualified_name", "No Category") == 'Main':
                command_signatures.append(
                    '-report <info> - Report a bug or problem')
            # pprint(command_signatures)
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                helpEmbed.add_field(name=cog_name, value="\n".join(
                    command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=helpEmbed)

    """async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            helpEmbed = discord.Embed(
                description=page, color=discord.Colour(settings['embedColor']))
            await destination.send(embed=helpEmbed)"""


intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(
    command_prefix=settings['botPrefix'], help_command=HelpCommand(), intents=intents)

with open('data/image.b64') as b:
    settings['botImageData'] = bytes(source=b.read(), encoding='utf-8')
    b.close()


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True, command_attrs={
        'name': 'setactivity',
    })
    async def setactivity(self, ctx, message):
        if not str(ctx.message.author.id) == str(settings['adminID']):
            return
        await bot.change_presence(activity=discord.Game(name=message))
        print(f'Activity set to "Playing {message}"')

    @commands.command(hidden=True, command_attrs={
        'name': 'test'
    })
    async def test(self, ctx, arg):
        await ctx.send(arg)
        print(arg)

    @commands.command(command_attrs={
        'name': 'report',
        'help': 'Sends a bug report to <@179757579759648769>',
        'cooldown': commands.Cooldown(1, 300.0, commands.BucketType.user)
    })
    async def report(self, ctx, *, message):
        # add reportblacklist.txt later if needed
        reportEmbed = discord.Embed(
            title='Report',
            description=f'**{message}**\nFrom: <@{ctx.message.author.id}>',
            color=discord.Colour(0x636363),
            timestamp=datetime.datetime.now())
        reportEmbed.set_footer(text=ctx.guild.name)
        await bot.get_channel(802599375674408991).send(embed=reportEmbed)
        await ctx.send('Report sent!')

    @commands.command(hidden=True, command_attrs={
        'name': 'uptime',
    })
    async def uptime(self, ctx):
        with open('uptime.txt', 'r') as u:
            startTime = u.read()
            u.close()
        tdelta = datetime.datetime.utcnow() - datetime.datetime.strptime(startTime,
                                                                         '%Y-%m-%d %H:%M:%S.%f')
        await ctx.send(f'`{tdelta}`')

    @commands.command(command_attrs={
        'name': 'info',
        'aliases': ['botinfo']
    })
    async def info(self, ctx):
        infoEmbed = discord.Embed(
            title='Info',
            description=f"""This bot was made by {settings['adminPing']}. If you encounter any bugs or issues, use the **-report** command or message me.
            For a full list of commands, use the **-help** command.
            Recommended server template for Mafia games (this bot will automatically set up the game if used in here): https://discord.new/WRPsR7HWrwBd."""
        )
        await ctx.send(embed=infoEmbed)


@bot.event
async def on_ready():
    # await bot.edit(avatar=settings['botImageData'])
    await bot.change_presence(activity=discord.Game(name='Mafia'))
    bot.add_cog(Main(bot))
    bot.add_cog(Game(bot))
    startTime = datetime.datetime.strftime(
        datetime.datetime.utcnow(), '%Y-%m-%d %H:%M:%S.%f')
    with open('uptime.txt', 'w') as u:
        u.write(str(startTime))
    """with open('data/emoji.json', 'w') as e:
        e.write(json.dumps({emoji.name: emoji.id for emoji in bot.emojis}))"""
    for guild in bot.guilds:
        await fixGuildFile(guild=guild)
    print('Logged on as {0.user}'.format(bot))


@bot.event
async def on_guild_join(guild):
    with open(f'games/{guild.id}.json', 'w') as guildFile:
        gameDict = {
            'guildName': guild.name,
            'guildID': guild.id,
            'metadata': defaultMetadata,
            'players': [],
            'rules': defaultRules,
            'roles': defaultRoles,
            'gameData': {
                'docHealedSelf': False
            }
        }
        # set up template recognition here
        guildFile.write(json.dumps(gameDict))
        guildFile.close()
    # template recognition
    templateRecognized = False
    for channel in guild.channels:
        if channel.name == 'read-channel-topic':
            if channel.topic.startswith(settings['templateRecogKey']):
                templateRecognized = True
    if templateRecognized:
        gen = None
        nameFormatter = {
            'village': 'villageChannel',
            'graveyard': 'graveyardChannel',
            'mafia-headquarters': 'mafiaChannel',
            'Alive': 'aliveRole',
            'Dead': 'deadRole'
        }
        with open(f'games/{guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        for channel in guild.channels:
            if channel.name == 'general':
                gen = channel
            elif channel.name in ('village', 'graveyard', 'mafia-headquarters'):
                guildDict['metadata'].update({
                    nameFormatter[channel.name]: channel.id
                })
        for role in guild.roles:
            if role.name in ('Alive', 'Dead'):
                guildDict['metadata'].update({
                    nameFormatter[role.name]: role.id
                })
        with open(f'games/{guild.id}.json', 'w') as guildFile:
            guildFile.write(json.dumps(guildDict))
        await gen.send(embed=discord.Embed(title='Template recognized!',
                                           color=discord.Colour(0x636363),
                                           timestamp=datetime.datetime.utcnow(),
                                           description='To see the current game settings, use `-viewsetup`.'))


async def fixGuildFile(guild):
    with open(f'games/{guild.id}.json', 'r') as guildFile:
        s = guildFile.read()
        if not len(s):  # if empty
            guildDict = {
                'guildName': guild.name,
                'guildID': guild.id,
                'metadata': defaultMetadata,
                'players': [],
                'rules': defaultRules,
                'roles': defaultRoles,
                'gameData': {
                    'docHealedSelf': False
                }
            }
        else:
            guildDict = json.loads(s)
        guildFile.close()
    with open(f'games/{guild.id}.json', 'w') as guildFile:
        sampleDict = {
            'guildName': guild.name,
            'guildID': guild.id,
            'metadata': defaultMetadata,
            'players': [],
            'rules': defaultRules,
            'roles': defaultRoles,
            'gameData': {
                'docHealedSelf': False
            }
        }
        for k, v in sampleDict.items():
            if k not in guildDict.keys():
                guildDict.update({k: v})
        guildDict['guildName'] = guild.name
        guildFile.write(json.dumps(guildDict))
        guildFile.close()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.type == 'private' or message.channel.type == 'group':
        await message.channel.send('This bot is currently disabled in DMs. Please try again in a server.')
        return
    try:
        await bot.process_commands(message)
    except:
        await message.channel.reply('An error occurred. Please try again.')

bot.run(settings['botToken'])
