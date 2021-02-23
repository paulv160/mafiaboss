from discord.ext import commands
from discord import *
from datetime import datetime
import time
import json
from pprint import pprint
# from utils import csvToList, listToCSV
import settings
from mafiagame import MafiaGame


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mafiaGame = None

    def dictSet(self, d):
        temp = dict()
        for k, v in d.items():
            if k not in temp.keys():
                temp.update({k: v})
        return temp

    def itemInDictKeys(self, i, d):
        for k in d.keys():
            if i == k:
                return True
        return False

    def removePlayerFromGame(self, guildID, playerID):
        with open(f'games/{guildID}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
            guildFile.close()
        with open(f'games/{guildID}.json', 'w') as guildFile:
            if playerID not in guildDict['players']:
                guildFile.close()
                return
            else:
                guildDict['players'].remove(playerID)
            guildFile.write(json.dumps(guildDict))
            guildFile.close()

    def updateIndex(self, guildID, guildName):
        return
        indexString = ''
        with open('games/index.json', 'r') as i:
            indexString = i.read()
            i.close()
        with open('games/index.json', 'w') as i:
            if len(indexString) == 0:
                indexDict = dict()
            else:
                indexDict = json.loads(indexString)
                # pprint(indexDict)
            if guildID in indexDict.keys():  # don't want to create dupes
                i.close()
                return
            else:
                indexDict.update({str(guildID): str(guildName)})
                # pprint(self.dictSet(indexDict))
                i.write(json.dumps(self.dictSet(indexDict)))
            i.close()

    def removeFromIndex(self, guildID):
        return
        with open('games/index.json', 'w') as i:
            indexDict = json.loads(i)
            if guildID not in indexDict.keys():
                i.close()
                return
            del indexDict[guildID]
            i.write(json.dumps(indexDict))
            i.close()

    def updateGame(self, guildID, userID):
        outcome = ''
        gameString = ''
        try:
            with open(f'games/{guildID}.json', 'r') as guildFile:
                guildDict = json.loads(gameString := guildFile.read())
            if userID in guildDict['players']:
                return 'You\'re already in the game!'
        except:
            pass
        with open(f'games/{guildID}.json', 'w') as guildFile:
            if len(gameString) == 0:
                outcome = 'Game created!'
                gameDict = {
                    'guildID': guildID,
                    'metadata': settings.defaultMetadata,
                    'players': [userID],
                    'rules': settings.defaultRules,
                    'roles': settings.defaultRoles
                }
                guildFile.write(json.dumps(gameDict))
                guildFile.close()
                return outcome
            else:
                outcome = 'Joined game!'
                gameDict = json.loads(gameString)
                if userID not in gameDict['players']:
                    gameDict['players'].append(userID)
                    # print(gameDict['players'])
            if len(gameDict['players']) > settings.smallRulesetLimit:
                gameDict['rules'] = settings.largeRules
            guildFile.write(json.dumps(gameDict))
        guildFile.close()
        return outcome

    async def initGuildFile(self, guildID):
        with open(f'games/{guildID}.json', 'w') as guildFile:
            guildDict = {
                'guildID': guildID,
                'metadata': settings.defaultMetadata,
                'players': [],
                'rules': settings.defaultRules,
                'roles': settings.defaultRoles
            }
            guildFile.write(json.dumps(guildDict))
            guildFile.close()

    async def hasAdminPerms(self, user):
        return user.guild_permissions.administrator

    @commands.command(command_attrs={
        'name': 'setup',
    })
    async def setup(self, ctx, villageChannel: TextChannel, graveyardChannel: TextChannel, mafiaChannel: TextChannel, aliveRole: Role, deadRole: Role):
        if not await self.hasAdminPerms(ctx.message.author):
            await ctx.reply('You need to be an administrator to use this command!')
            return
        else:
            invalidArgNames = []
            if type(villageChannel) != TextChannel or type(graveyardChannel) != TextChannel or type(mafiaChannel) != TextChannel or type(aliveRole) != Role or type(deadRole) != Role:
                if type(villageChannel) != TextChannel:
                    invalidArgNames.append('villageChannel')
                if type(graveyardChannel) != TextChannel:
                    invalidArgNames.append('graveyardChannel')
                if type(aliveRole) != Role:
                    invalidArgNames.append('aliveRole')
                if type(deadRole) != Role:
                    invalidArgNames.append('deadRole')
                await ctx.reply(f'These arguments were invalid: {", ".join(invalidArgNames)}. Please try again.')
                return
            else:
                with open(f'games/{ctx.guild.id}.json', 'r') as guildFile:
                    if len(guildFile.read()) == 0:
                        await self.initGuildFile(ctx.guild.id)
                    guildFile.seek(0)
                    # pprint(guildFile.read())
                    guildDict = json.loads(guildFile.read())
                    guildFile.close()
                with open(f'games/{ctx.guild.id}.json', 'w') as guildFile:
                    guildDict['metadata'].update({
                        'villageChannel': villageChannel.id,
                        'graveyardChannel': graveyardChannel.id,
                        'mafiaChannel': mafiaChannel.id,
                        'aliveRole': aliveRole.id,
                        'deadRole': deadRole.id
                    })
                    # pprint(guildDict)
                    guildFile.write(json.dumps(guildDict))
                    guildFile.close()
        await ctx.send('Setup complete! Use -viewsetup to verify that it worked.')

    @commands.command(command_attrs={
        'name': 'viewsetup',
    })
    async def viewsetup(self, ctx):
        with open(f'games/{ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        md = guildDict['metadata']
        vc = f'<#{md["villageChannel"]}>' if md['villageChannel'] is not None else 'No channel selected'
        gc = f'<#{md["graveyardChannel"]}>' if md['graveyardChannel'] is not None else 'No channel selected'
        mc = f'<#{md["mafiaChannel"]}>' if md['mafiaChannel'] is not None else 'No channel selected'
        ar = f'<@&{md["aliveRole"]}>' if md['aliveRole'] is not None else 'No role selected'
        dr = f'<@&{md["deadRole"]}>' if md['deadRole'] is not None else 'No role selected'
        setupViewEmbed = Embed(
            title=f'**Current Game Channels/Roles:**',
            color=Colour(0x636363),
            timestamp=datetime.utcnow(),
            description=f"""**Village Channel** - this is where the alive villagers (and mafia) will be able to talk and where voting will take place - {vc}
        **Graveyard Channel** - this is where only villagers and mafia who have been killed or hung will be able to talk - {gc}
        (Both of the above can optionally have voice channels in addition to text channels for easier discussion.)
        **Mafia Channel** - if you play with more than 1 Mafia, this is where they'll choose their targets. - {mc}
        **Alive Role** - this role will be given to those currently in the game - {ar}
        **Dead Role** - once you die, you lose the alive role and receive this instead, allowing you to talk in the graveyard - {dr}
        
        Please note that the channel and role names do not matter, they just must be assigned with -setup (by a server admin) and that they work properly (for example, dead people should not be allowed to talk in #village).
        For an easier time setting everything up, consider using this server template: https://discord.com/template/WRPsR7HWrwBd as the bot will recognize it and you will not have to use -setup.""")
        await ctx.send(embed=setupViewEmbed)

    @commands.command(command_attrs={
        'name': 'rules'
    })
    async def rules(self, ctx):
        embed = Embed(title='Game Rules & Roles',
                      color=Colour(0x636363),
                      timestamp=datetime.utcnow(),
                      description="""**Mafia** - As the Mafia, your goal is to kill all the villagers, and you can do so once per night. You win the game when there is 1 Mafia left alive for every living villager.
        **Doctor** - You can save a person of your choice once per night from being killed by the Mafia. You can save yourself too, but only once per game!
        **Detective** - You can investigate one person per night to see if they're the Mafia or they're just an innocent.

        Note: Be careful with voting and choosing your targets, as the ability to change your target hasn't been added yet.
        """)
        await ctx.send(embed=embed)

    @commands.command(command_attrs={
        'name': 'join',
        'aliases': ['joingame']
    })
    async def join(self, ctx):
        self.updateIndex(ctx.guild.id, ctx.guild.name)
        await ctx.send(self.updateGame(ctx.guild.id, ctx.author.id))

    @commands.command(command_attrs={
        'name': 'leave',
        'aliases': ['leavegame']
    })
    async def leave(self, ctx):
        self.removePlayerFromGame(ctx.guild.id, ctx.message.author.id)

    @commands.command(command_attrs={
        'name': 'clear',
    })
    async def clear(self, ctx):
        if self.mafiaGame is not None:
            del self.mafiaGame
            self.mafiaGame = None
            await ctx.send('Game over!')
        with open(f'games/{ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        with open(f'data/emoji_map.json', 'r') as emojiMap:
            emojiDict = json.loads(emojiMap.read())
        if len(guildDict['players']) == 0:
            await ctx.message.add_reaction(emojiDict['no_entry_sign'])
            await ctx.reply('The lobby is empty!')
        elif Permissions(administrator=True) not in ctx.author.guild_permissions and ctx.author.id != guildDict['players'][0]:
            #print(type(emojiDict))
            await ctx.message.add_reaction(emojiDict['no_entry_sign'])
            await ctx.reply('You need to be the owner of the game or a server admin to use this command!')
        else:
            guildDict['players'] = []
            with open(f'games/{ctx.guild.id}.json', 'w') as guildFile:
                guildFile.write(json.dumps(guildDict))
            await ctx.message.add_reaction(emojiDict['white_check_mark'])

    @commands.command(command_attrs={
        'name': 'kill',
    })
    async def kill(self, ctx):
        with open(f'games/{ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        with open(f'data/emoji_map.json', 'r') as emojiMap:
            emojiDict = json.loads(emojiMap.read())
        if len(guildDict['players']) == 0:
            await ctx.message.add_reaction(emojiDict['no_entry_sign'])
            await ctx.reply('The lobby is empty!')
            return
        if Permissions(administrator=True) not in ctx.author.guild_permissions and ctx.author.id != guildDict['players'][0]:
            await ctx.message.add_reaction(emojiDict['no_entry_sign'])
            await ctx.reply('You need to be the owner of the game or a server admin to use this command!')
            return
        #print(self.mafiaGame)
        if self.mafiaGame is not None:
            del self.mafiaGame
            self.mafiaGame = None
            await ctx.message.add_reaction(emojiDict['white_check_mark'])
            await ctx.send('Game over!')
        else:
            await ctx.message.add_reaction(emojiDict['no_entry_sign'])
            await ctx.send('No game is currently active. Did you want to **clear** the lobby?')

    @commands.command(command_attrs={
        'name': 'game',
        'aliases': ['view', 'viewgame']
    })
    async def game(self, ctx):
        with open(f'games/{ctx.message.guild.id}.json', 'r') as g:
            if len(g.read()) == 0:
                await ctx.send(f'No game has been made yet!')
                g.close()
                return
            else:
                g.seek(0)  # go back to the start of the file
                guildGameDict = json.loads(g.read())
            g.close()
        mentionList = [f'<@{ID}>\n' for ID in guildGameDict['players']]
        if len(mentionList) > 0:
            mentionList[0] = mentionList[0][:-1] + ' - Owner\n'
        playerListStr = f'**Current Players:**\n{"".join(mentionList)}' if len(
            guildGameDict['players']) > 0 else '**Current Players:**\nNone'
        gameViewEmbed = Embed(
            title='Mafia',
            description=playerListStr,
            color=Colour(0x636363),
            timestamp=datetime.utcnow())
        gameViewEmbed.set_footer(text=ctx.guild.name)
        await ctx.send(embed=gameViewEmbed)

    @commands.command(command_attrs={
        'name': 'start',
        'aliases': ['startgame']
    })
    async def start(self, ctx):
        with open(f'games/{ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
            guildFile.close()
        # if any of the metadata values have not been init'd
        if None in guildDict['metadata'].values():
            await ctx.send('Make sure to set up all channels and roles before starting a game!')
            return
        elif len(guildDict['players']) < settings.minPlayers:
            await ctx.reply(f'You must have at least {settings.minPlayers} players before starting a game! You currently have {len(guildDict["players"])}.')
        else:
            await ctx.send('Starting game!')
            self.mafiaGame = MafiaGame(self.bot, ctx)
            try:
                await self.mafiaGame.run()
            except Exception as e:
                await ctx.reply(
                    f'Game over! An error occurred. Please use the `report` command to report the problem:\n`{str(e)}`')
