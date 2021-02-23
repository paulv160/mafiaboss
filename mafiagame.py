import random
import discord
from datetime import datetime
from discord.ext import *
from discord.utils import get
import math
import itertools
import re
import json
import asyncio
from pprint import pprint
import settings


def repInt(string, bounds=None):
    try:
        num = int(string)
        return bounds[0] <= num <= bounds[1] if bounds else True
    except ValueError:
        return False


def repUserID(string, bot):
    return bot.get_user(int(string)) is not None if repInt(string) else False


class MafiaGame:
    def __init__(self, bot, invokeContext):
        self.bot = bot
        self.ctx = invokeContext
        self.gameInitialized = False
        self.deathMsgs = ('**PLAYER_NAME** was bludgeoned to death with a hammer.', '**PLAYER_NAME** was thrown into a shark tank.',
                          '**PLAYER_NAME**\'s head was found rolling around in the **GUILD_NAME** town square.', '**PLAYER_NAME** was strangled with an extension cord.')
        self.voteMsgs = ('**PLAYER_NAME** was sentenced to death by their fellow villagers.',
                         '**PLAYER_NAME** was put under the guillotine.')
        self.dayNightStages = ({
            'name': 'Day ',
            'msgToShow': '**Daytime**',
            'imageToShow': 'day.png',
            'msgWhenDone': '',
            'action': 'player_vote'
        },
            {
            'name': 'Night ',
            'msgToShow': '**Nighttime**',
            'imageToShow': 'night.png',
            'msgWhenDone': '',
            'action': 'player_actions'
        })
        self.initialStage = {
            'name': 'roleAssignment',
            'msgToShow': 'Choosing roles...',
            'imageToShow': None,
            'msgWhenDone': 'Roles assigned!',
            'action': 'choose_roles'
        }

    def messageRelatesToCurrGame(self, m):
        if m.author.bot:
            return False
        if m.guild == None:  # if in a dm
            # if user is not in ctx.guild
            if self.ctx.guild.get_member(m.author.id) is None:
                return False
            else:  # if msg in dm, user in this guild
                return True
        elif m.guild != self.ctx.guild:
            return False
        else:  # if in this guild
            return True

    async def fixPermissions(self, enableAll=False):
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        guildDict['gameData'] = settings.defaultGameData
        with open(f'games/{self.ctx.guild.id}.json', 'w') as guildFile:
            guildFile.write(json.dumps(guildDict))

        aliveRole = get(self.ctx.guild.roles,
                        id=guildDict['metadata']['aliveRole'])
        deadRole = get(self.ctx.guild.roles,
                       id=guildDict['metadata']['deadRole'])
        mafiaChannel = get(self.ctx.guild.channels,
                           id=guildDict['metadata']['mafiaChannel'])
        pprint(guildDict)
        for k, role in guildDict['roles'].items():
            for player in role:
                if enableAll:
                    player[1] = True
                if player[1]:  # if alive
                    member = await self.ctx.guild.fetch_member(player[0])
                    await member.add_roles(aliveRole)
                    await member.remove_roles(deadRole)
                    if k == 'mafia':
                        perms = mafiaChannel.overwrites_for(member)
                        """await mafiaChannel.edit(overwrites={
                            member: discord.PermissionOverwrite(
                                view_channel=True, read_messages=True, send_messages=True)
                        })"""
                        perms.read_messages = True
                        perms.send_messages = True
                        perms.view_channel = True
                        await mafiaChannel.set_permissions(member, overwrite=perms)
                        print(
                            f'{self.bot.get_user(player[0]).name} has been given mafia perms')
                    else:
                        perms = mafiaChannel.overwrites_for(member)
                        """await mafiaChannel.edit(overwrites={
                            member: discord.PermissionOverwrite(
                                view_channel=True, read_messages=True, send_messages=True)
                        })"""
                        perms.read_messages = False
                        perms.send_messages = False
                        perms.view_channel = False
                        await mafiaChannel.set_permissions(member, overwrite=perms)
                        print(
                            f'{self.bot.get_user(player[0]).name} has lost mafia perms')
                    print(
                        f'{self.bot.get_user(player[0]).name} has been given alive perms')
                else:  # if dead
                    member = await self.ctx.guild.fetch_member(player[0])
                    await member.add_roles(deadRole)
                    perms = mafiaChannel.overwrites_for(member)
                    """await mafiaChannel.edit(overwrites={
                        member: discord.PermissionOverwrite(
                            view_channel=True, read_messages=True, send_messages=True)
                    })"""
                    perms.read_messages = False
                    perms.send_messages = False
                    perms.view_channel = False
                    await mafiaChannel.set_permissions(member, overwrite=perms)
                    print(
                        f'{self.bot.get_user(player[0]).name} has been given dead perms')

    async def initGame(self):
        self.gameInitialized = True
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        # print(len(guildDict['players']) - guildDict['rules']['mafia'] - guildDict['rules']['doctor'] - guildDict['rules']['detective'])
        guildDict['rules'].update({
            'villager': len(guildDict['players']) - guildDict['rules']['mafia'] - guildDict['rules']['doctor'] - guildDict['rules']['detective'],
        })
        guildDict['roles'].update({
            'villager': [],
            'mafia': [],
            'doctor': [],
            'detective': []
        })
        # pprint(guildDict['rules'])
        roleFreqList = []
        for k, v in guildDict['rules'].items():
            roleFreqList += [k]*v  # nice way to do it
        # print(len(roleFreqList))
        # pprint(roleFreqList)
        randRoles = random.sample(guildDict['players'], k=len(roleFreqList))
        for rolename, playerID in zip(roleFreqList, randRoles):
            # print(rolename, self.bot.get_user(playerID).id)
            if rolename in guildDict['roles'].keys():
                guildDict['roles'][rolename].append([playerID, True])
            else:
                guildDict['roles'].update({rolename: []})
                guildDict['roles'][rolename].append([playerID, True])
            userObj = self.bot.get_user(playerID)
            await userObj.send(f'You are {"the" if roleFreqList.count(rolename) == 1 else ("an" if rolename[0:1] in "aeiou" else "a")} {rolename.upper()}!')
        # pprint(guildDict)
        # am i done here? nope, dm the people, write to the file
        with open(f'games/{self.ctx.guild.id}.json', 'w') as guildFile:
            guildFile.write(json.dumps(guildDict))
        # delete later
        for k, v in guildDict['roles'].items():
            for lst in v:
                # await self.ctx.send(f'<@{lst[0]}> is {k}')
                pass
        await self.fixPermissions(enableAll=True)

    # these methods return the ID of the player that was chosen
    async def messageMafia(self, ID, guildDict):
        nonMafiaPlayers = []
        for roleName, roleList in guildDict['roles'].items():
            if roleName == 'mafia':
                continue
            for playerList in roleList:
                if playerList[1]:  # if alive
                    nonMafiaPlayers.append(playerList[0])
        formattedList = '\n' + \
            '\n'.join([f'{n}: <@{ID}>' for n,
                       ID in enumerate(nonMafiaPlayers, start=1)])
        # this way, the user choice will be the right index for this list
        indexedChoices = [None] + nonMafiaPlayers
        embed = discord.Embed(
            title=f'**{settings.roleEmbedTitles["mafia"]}**',
            color=discord.Colour(0x636363),
            timestamp=datetime.utcnow(),
            description=f'Type `kill [num]` to kill someone.{formattedList}')
        await self.bot.get_user(ID).send(embed=embed)

        def check(m, ID, bot, ICL):
            if not self.messageRelatesToCurrGame(m):
                return False
            r = random.randint(0, 50)
            args = m.content.split(' ')
            if m.author.id != ID:
                return False
            elif args[0].lower() != 'kill':
                return False
            else:
                try:
                    return repUserID(ICL[int(re.sub('[!@<>]', '', args[1]))], bot)
                except ValueError:
                    return False
                except IndexError:
                    return False

        res = await self.bot.wait_for('message', check=lambda m: check(m, ID, self.bot, indexedChoices))
        print(f'res done in mafia')
        target = indexedChoices[int(res.content.split(' ')[1])]
        await self.bot.get_user(ID).send(f'You have chosen to kill <@{target}>!')
        return target

    async def messageMafias(self, IDList, guildDict):
        nonMafiaPlayers = []
        for roleName, roleList in guildDict['roles'].items():
            if roleName == 'mafia':
                continue
            for playerList in roleList:
                if playerList[1]:  # if alive
                    nonMafiaPlayers.append(playerList[0])  # fix later
                    """print(nonMafiaPlayers)
                    print('/')
                    print(IDList)"""

        formattedList = '\n' + \
            '\n'.join([f'{n}: <@{ID}>' for n,
                       ID in enumerate(nonMafiaPlayers, start=1)])

        # this way, the user choice will be the right index for this list
        indexedChoices = [None] + nonMafiaPlayers
        embed = discord.Embed(
            title=f'**{settings.roleEmbedTitles["mafia"]}**',
            color=discord.Colour(0x636363),
            timestamp=datetime.utcnow(),
            description=f'Type `kill [num]` to kill someone. The first choice from any of you will count, so choose wisely! {formattedList}')
        await self.bot.get_channel(guildDict['metadata']['mafiaChannel']).send(embed=embed)

        def check(m, IDList, bot, ICL):
            if not self.messageRelatesToCurrGame(m):
                return False
            r = random.randint(0, 50)
            args = m.content.split(' ')
            if m.author.id not in IDList:
                return False
            elif args[0].lower() != 'kill':
                return False
            else:
                try:
                    return repUserID(ICL[int(re.sub('[!@<>]', '', args[1]))], bot)
                except ValueError:
                    return False
                except IndexError:
                    return False

        res = await self.bot.wait_for('message', check=lambda m: check(m, IDList, self.bot, indexedChoices))
        print(f'res done in multi mafia')
        target = indexedChoices[int(res.content.split(' ')[1])]
        await self.bot.get_channel(guildDict['metadata']['mafiaChannel']).send(f'You have chosen to kill <@{target}>!')
        return target

    async def messageDoctor(self, ID, guildDict):
        nonDoctorPlayers = []
        for roleName, roleList in guildDict['roles'].items():
            if roleName == 'doctor':
                continue  # very bad but works
            for playerList in roleList:
                if playerList[1]:  # if alive
                    nonDoctorPlayers.append(playerList[0])
        if not guildDict['gameData']['docHealedSelf']:
            nonDoctorPlayers.append(ID)
        formattedList = '\n' + \
            '\n'.join([f'{n}: <@{ID}>' for n,
                       ID in enumerate(nonDoctorPlayers, start=1)])
        indexedChoices = [None] + nonDoctorPlayers
        embed = discord.Embed(title=f'**{settings.roleEmbedTitles["doctor"]}**',
                              color=discord.Colour(0x636363),
                              timestamp=datetime.utcnow(),
                              description=f'Type `heal [num]` to heal someone.{formattedList}')
        await self.bot.get_user(ID).send(embed=embed)

        def check(m, ID, bot, ICL):
            if not self.messageRelatesToCurrGame(m):
                return False
            r = random.randint(0, 50)
            args = m.content.split(' ')
            if m.author.id != ID:
                return False
            elif args[0].lower() != 'heal':
                return False
            else:
                try:
                    return repUserID(ICL[int(re.sub('[!@<>]', '', args[1]))], bot)
                except ValueError:
                    return False
                except IndexError:
                    return False

        res = await self.bot.wait_for('message', check=lambda m: check(m, ID, self.bot, indexedChoices))
        print(f'res done in doc')
        target = indexedChoices[int(res.content.split(' ')[1])]
        if target == ID:
            guildDict['gameData']['docHealedSelf'] = True
            with open(f'games/{self.ctx.guild.id}.json', 'w') as guildFile:
                guildFile.write(json.dumps(guildDict))
            await self.bot.get_user(ID).send(f'You have chosen to heal yourself!')
        else:
            await self.bot.get_user(ID).send(f'You have chosen to heal <@{target}>!')
        return target

    async def messageDetective(self, ID, guildDict):
        nonDetectivePlayers = []
        for roleName, roleList in guildDict['roles'].items():
            if roleName == 'detective':
                continue
            for playerList in roleList:
                if playerList[1]:  # if alive
                    nonDetectivePlayers.append(playerList[0])
        formattedList = '\n' + \
            '\n'.join([f'{n}: <@{ID}>' for n,
                       ID in enumerate(nonDetectivePlayers, start=1)])
        indexedChoices = [None] + nonDetectivePlayers
        embed = discord.Embed(title=f'**{settings.roleEmbedTitles["detective"]}**',
                              color=discord.Colour(0x636363),
                              timestamp=datetime.utcnow(),
                              description=f'Type `check [num]` to investigate someone.{formattedList}')
        await self.bot.get_user(ID).send(embed=embed)

        def check(m, ID, bot, ICL):
            if not self.messageRelatesToCurrGame(m):
                return False
            r = random.randint(0, 50)
            args = m.content.split(' ')
            if m.author.id != ID:
                return False
            elif args[0].lower() != 'check':
                return False
            else:
                try:
                    return repUserID(ICL[int(re.sub('[!@<>]', '', args[1]))], bot)
                except ValueError:
                    return False
                except IndexError:
                    return False

        res = await self.bot.wait_for('message', check=lambda m: check(m, ID, self.bot, indexedChoices))
        print(f'res done in det')
        target = indexedChoices[int(res.content.split(' ')[1])]
        await self.bot.get_user(ID).send(f'You have chosen to investigate <@{target}>!')
        return target

    async def killPlayer(self, ID, causeOfDeath):
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        for role in guildDict['roles'].values():
            for player in role:
                if player[0] == ID:
                    # print('found one in kp')
                    player[1] = False
        with open(f'games/{self.ctx.guild.id}.json', 'w') as guildFile:
            guildFile.write(json.dumps(guildDict))
        if ID is None:
            print(f'ID is "{ID}"')
        return random.choice(self.voteMsgs) if causeOfDeath == 'vote' else f'{random.choice(self.deathMsgs).replace("GUILD_NAME", self.ctx.guild.name).replace("PLAYER_NAME", self.bot.get_user(ID).name)}'

    async def getRole(self, ID):
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        for k, role in guildDict['roles'].items():
            for player in role:
                if player[0] == ID:
                    return k
        return None

    async def execDay(self, dayDict):
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        # pprint(guildDict)
        # go through all roles, compile living players into a list
        livingPlayers = []
        for roleList in guildDict['roles'].values():
            for playerList in roleList:
                if playerList[1]:
                    livingPlayers.append(playerList[0])
        # make a check function (m.content.lower().startswith('vote'))
        submitted = []

        voteDict = {lp: 0 for lp in livingPlayers}

        def addVote(pID):
            nonlocal voteDict
            voteDict[pID] += 1

        def removeVote(pID):
            pass

        def voteEvaluator(d):  # returns the dict key with the highest val, or None if tie
            maxVotes = 0
            maxKeys = []
            for k, v in d.items():
                if v > maxVotes:
                    maxVotes = v
                    maxKeys = [k]
                elif v == maxVotes:
                    maxKeys.append(k)
                else:  # if it's less
                    pass
            return maxKeys[0] if len(maxKeys) == 1 else None

        def check(message, validIDList):
            if not self.messageRelatesToCurrGame(message):
                return False, False, None, None
            nonlocal submitted, voteDict
            if message.content.lower() == 'skip':
                return False, True, 'Skipped!', None
            if message.author.id not in validIDList:
                return False, False, 'You don\'t seem to be able to vote (you might be dead or not in the game).', None
            elif len((args := message.content.split())) != 2:
                return False, False, 'Who do you want to vote for?', None
            else:
                if message.author.id in submitted:
                    # FIX THIS LATER LOL
                    return False, False, 'You can only vote once! (The ability to change your vote hasn\'t been added yet)', None
                if args[0].lower() == 'vote' and repUserID(re.sub('[!@<>]', '', args[1]), self.bot):
                    try:
                        _ = voteDict[int(re.sub('[!@<>]', '', args[1]))]
                        submitted.append(message.author.id)
                        return True, False, 'Vote received!', int(re.sub('[!@<>]', '', args[1]))
                    except KeyError:
                        return False, False, 'That player seems to be dead or not in the game! Please try again.', None
                return False, False, 'Something went wrong. Please try again.', None

        embed = discord.Embed(
            title='Voting Time!', description=f'Type `vote [user]` to vote for who you think is the Mafia, or `skip` to skip.')
        await self.ctx.send(embed=embed)

        while True:
            msg = await self.bot.wait_for('message', check=lambda m: True)
            voteRecognized, skipRecognized, reply, retID = check(
                msg, livingPlayers)
            if reply is not None:  # if messageRelatesToCurrGame
                if voteRecognized:
                    submitted.append(msg.author.id)
                    addVote(retID)
                    print(
                        f'vote from {msg.author.name} for {self.bot.get_user(retID).name} recognized')
                elif skipRecognized:
                    submitted.append(msg.author.id)
                    print(f'skip from {msg.author.name} recognized')
                else:
                    print(f'vote from {msg.author.name} not recognized')
                await msg.reply(reply)
                if frozenset(livingPlayers) == frozenset(submitted):  # hope this doesnt break
                    await self.ctx.send('All votes are in!')
                    # await self.ctx.send(str(voteDict))
                    break

        voteStr = ''
        if (voteRes := voteEvaluator(voteDict)) is not None:
            user = self.bot.get_user(int(voteRes))
            _ = await self.killPlayer(int(voteRes), 'vote')
            await self.fixPermissions()
            voteStr = random.choice(self.voteMsgs).replace(
                'PLAYER_NAME', f'<@{user.id}>')
        else:
            voteStr = 'No one was voted out.'
        voteResultEmbed = discord.Embed(
            color=discord.Colour(0x636363),
            timestamp=datetime.utcnow(),
            title='All votes are in!', description=voteStr)
        await self.ctx.send(embed=voteResultEmbed)

    async def execNight(self, nightDict):
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
            guildFile.close()
        livingMafia, livingDoctors, livingDetectives = [], [], []

        embed = discord.Embed(
            title='Nighttime', description=f'Follow the instructions in your DMs if you have a role.')
        await self.ctx.send(embed=embed)

        # dm all people
        # go through all roles, if none are alive for that role, skip
        # else, make lists of living mafia, doctors, detectives
        for playerList in guildDict['roles']['mafia']:
            if playerList[1]:
                livingMafia.append(playerList[0])
        for playerList in guildDict['roles']['doctor']:
            if playerList[1]:
                livingDoctors.append(playerList[0])
        for playerList in guildDict['roles']['detective']:
            if playerList[1]:
                livingDetectives.append(playerList[0])
        # make a generic check function with 3 params: message, IDList, action ('kill')

        def check(message, IDList, action):
            if message.author.id not in IDList:
                return False
            elif len((args := message.content.split())) != 2:
                return False
            else:
                if args[0].lower() == action and repUserID(re.sub('[!@<>]', '', args[1]), self.bot):
                    return True
                return False
        # make a list of lambdas from this and the list of lists of living roles
        checkList = []
        mafiaTaskList, doctorTaskList, detectiveTaskList = [], [], []

        ret = 55.8
        livingRoleTargetDictKeys = []
        if livingMafia:
            if len(livingMafia) == 1:
                mafiaTaskList.append(self.messageMafia(
                    livingMafia[0], guildDict))
            else:
                mafiaTaskList.append(self.messageMafias(
                    livingMafia, guildDict))
            checkList.append(lambda m: check(m, livingMafia, 'kill'))
            livingRoleTargetDictKeys.append('mafia')
        if livingDoctors:
            doctorTaskList.append(self.messageDoctor(
                livingDoctors[0], guildDict))
            checkList.append(lambda m: check(m, livingDoctors, 'heal'))
            livingRoleTargetDictKeys.append('doctor')
        if livingDetectives:
            detectiveTaskList.append(self.messageDetective(
                livingDetectives[0], guildDict))
            checkList.append(lambda m: check(
                m, livingDetectives, 'investigate'))
            livingRoleTargetDictKeys.append('detective')
        # print('lens are', len(mafiaTaskList), len(doctorTaskList), len(detectiveTaskList))
        messageTaskList = mafiaTaskList + doctorTaskList + detectiveTaskList
        # put these into gather
        ret = await asyncio.gather(*messageTaskList)
        # await asyncio.gather(*[self.bot.wait_for('message', check=c) for c in checkList])
        print('all actions received!')
        # pprint(ret)
        retZip = dict(zip(livingRoleTargetDictKeys, ret))

        # handling night events
        kp = None  # killedPlayer
        deathMsg = None
        docTarget = None
        try:
            docTarget = retZip['doctor']
        except KeyError:
            pass
        if 'mafia' in retZip.keys():
            if retZip['mafia'] != docTarget:
                kp = retZip['mafia']
                print(deathMsg := await self.killPlayer(kp, 'mafia'))

        try:
            detectiveRes = 'is an innocent' if await self.getRole(retZip['detective']) != 'mafia' else 'is a Mafia'
            await self.bot.get_user(livingDetectives[0]).send(f'<@{retZip["detective"]}> {detectiveRes}.')
        except KeyError:
            pass
        await self.fixPermissions()
        kpStr = 'Fortunately, no one died.' if not kp else deathMsg
        nightEmbed = discord.Embed(title='Morning',
                                   color=discord.Colour(0x636363),
                                   timestamp=datetime.utcnow(),
                                   description=kpStr)
        await self.ctx.send(embed=nightEmbed)

    def gameWinner(self):
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        livingMafias, livingVillagers = 0, 0
        for rolename, rolelist in guildDict['roles'].items():
            for player in rolelist:
                if player[1]:
                    if rolename == 'mafia':
                        livingMafias += 1
                    else:
                        livingVillagers += 1
        if not livingMafias:
            return 'villager'
        else:
            return 'mafia' if livingMafias >= livingVillagers else 'none'

    def stageGen(self, i=0):
        if i == 0:
            yield self.initialStage
        else:
            yieldStage = self.dayNightStages[i % 2]
            yieldStage['name'] = re.sub(
                '( [0-9]*)', f' {math.ceil(i/2)}', yieldStage['name'])
            # pprint(yieldStage)
            yield yieldStage

    async def generateRandomDeathMessage(self):
        return f'**PLAYER_NAME**{random.choice(self.deathMsgs)}'

    async def getGameOwnerID(self) -> discord.User:
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
        return guildDict['players'][0]

    async def endGame(self, winnerStr):
        embed = discord.Embed(
            color=discord.Colour(0x636363),
            timestamp=datetime.utcnow()
        )
        if winnerStr == 'mafia':
            embed.title = 'Mafia wins!'
        elif winnerStr == 'villager':
            embed.title = 'Villagers win!'
        await self.ctx.send(embed=embed)
        await self.fixPermissions(enableAll=True)

    async def run(self):
        self.gameInitialized = False
        for i in range(50):
            # ownerID = await self.getGameOwnerID()
            dct = next(self.stageGen(i=i))
            if dct['name'] == 'roleAssignment':
                if not self.gameInitialized:
                    await self.initGame()
            elif dct['name'].startswith('Day'):
                await self.execDay(dct)
                if (gw := self.gameWinner()) != 'none':
                    await self.endGame(gw)
                    return
                print('day done')
            elif dct['name'].startswith('Night'):
                await self.execNight(dct)
                if (gw := self.gameWinner()) != 'none':
                    await self.endGame(gw)
                    return
                print('night done')
