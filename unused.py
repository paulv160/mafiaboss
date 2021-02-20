import random
import discord
from discord.ext import *
import math
import itertools
import re
import json
import asyncio
from pprint import pprint
import settings


class MafiaGame:
    def __init__(self, bot, invokeContext):
        self.bot = bot
        self.ctx = invokeContext
        self.gameInitialized = False
        self.deathMsgs = ('**PLAYER_NAME** was bludgeoned to death with a hammer.', '**PLAYER_NAME** was thrown into a shark tank.',
                          '**PLAYER_NAME**\'s head was found rolling around in the **GUILD_NAME** town square.', '**PLAYER_NAME** was strangled with an extension cord.')
        self.voteMsg = '**PLAYER_NAME** was sentenced to death by their fellow villagers.'
        self.dayNightStages = ({
            'name': 'Day ',
            'msgToShow': '**Daytime**',
            'imageToShow': 'day.png',
            'msgWhenDone': self.voteMsg,
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

    # targetInfo = [channelID/None, None/userID of dm]
    async def waitForAction(self, action, targetInfo):  # playerIDList
        if targetInfo[0] is None:  # dm
            def check(m):
                # 'vote' or #'kill'
                return m.guild is None and m.author.id == targetInfo[1] and m.content.startswith(action)
            return await self.bot.wait_for('message', check=check)
        else:  # channel
            def check(m):
                if m.channel is None:
                    return False
                return m.channel.id == targetInfo[0] and m.content.startswith(action)
            return await self.bot.wait_for('message', check=check)

    async def healPlayer(self, playerID):
        pass

    async def investigatePlayer(self, playerID):
        pass

    async def killPlayer(self, playerID, role, causeOfDeath):  # 'mafia' or 'vote'
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
            guildFile.close()
        with open(f'games/{self.ctx.guild.id}.json', 'w') as guildFile:
            for v in guildDict['roles'].values():
                for sublist in v:
                    print(sublist, playerID)
                    if sublist[0] == playerID:
                        sublist[1] = False
            else:
                print('Error in killPlayer!')
            guildFile.write(json.dumps(guildDict))
            guildFile.close()
        return self.voteMsg if causeOfDeath == 'vote' else f'{random.choice(self.deathMsgs).replace("GUILD_NAME", self.ctx.guild.name).replace("PLAYER_NAME", self.bot.get_user(playerID).name)}'

    async def initGame(self):
        self.gameInitialized = True
        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
            guildFile.close()
        #print(len(guildDict['players']) - guildDict['rules']['mafia'] - guildDict['rules']['doctor'] - guildDict['rules']['detective'])
        guildDict['rules'].update({
            'villager': len(guildDict['players']) - guildDict['rules']['mafia'] - guildDict['rules']['doctor'] - guildDict['rules']['detective'],
        })
        del guildDict['roles']['villager']
        del guildDict['roles']['doctor']
        del guildDict['roles']['detective']
        del guildDict['roles']['mafia']
        # pprint(guildDict['rules'])
        roleFreqList = []
        for k, v in guildDict['rules'].items():
            roleFreqList += [k]*v  # nice way to do it
        # print(len(roleFreqList))
        # pprint(roleFreqList)
        randRoles = random.sample(guildDict['players'], k=len(roleFreqList))
        for rolename, playerID in zip(roleFreqList, randRoles):
            #print(rolename, self.bot.get_user(playerID).id)
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
            guildFile.close()
        # delete later
        for k, v in guildDict['roles'].items():
            for lst in v:
                await self.ctx.send(f'<@{lst[0]}> is {k}')

    async def execDay(self, dct):
        def repInt(string):
            try:
                int(string)
                return True
            except ValueError:
                return False

        def check(m, userID):
            if m.author.id != userID:
                return False
            else:
                args = m.content.split(' ')
                if len(args) == 2:
                    if args[0] == 'vote' and repInt(args[1][2:-1]):
                        return True
                elif len(args) == 3:
                    if f'{args[0]} {args[1]}' == 'vote for' and repInt(args[2][2:-1]):
                        return True
                return False

        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
            guildFile.close()

        playerObjList = []  # list of lists
        for roleList in guildDict['roles'].values():
            for playerList in roleList:
                if playerList[1] is True:
                    playerObjList.append(playerList)

        checkList = [lambda m: check(m, ID) for ID in playerObjList]
        taskList = [self.bot.wait_for(
            'message', timeout=10, check=c) for c in checkList]
        ret = await asyncio.gather(*[await i for i in taskList])
        await self.ctx.send("everyone has voted")

    async def execNight(self, dct):
        def check(m, listLength, lastMessage):  # if list is [1, 2] LL = 2
            # if message is from the player, contains a valid int only, and is in range of the list

            def repInt(string):
                try:
                    int(string)
                    return True
                except ValueError:
                    return False

            if not repInt(m.content):
                return False
            elif m.author == self.bot.user:
                return False
            else:
                return 0 < int(m.content)-1 <= listLength

        # returns kill message, killed user
        async def execMafia(self, playerID, targetDict):
            # if no mafias are alive, return None for the user
            # pprint(targetDict)
            for mafiaList in targetDict['mafia']:
                if mafiaList[1] is True:
                    break
            else:
                return 'No one was killed.', None
            msgAlreadySent = False
            targetList = []
            for k, v in targetDict.items():
                if k != 'mafia':
                    if type(v[0]) is list:
                        for sublist in v:
                            if playerID in sublist:
                                print('This player is not a mafia!')
                                return 'you fucked up :)', None
                            if sublist[0] is not playerID and sublist[1]:  # if alive
                                targetList.append(sublist[0])
                                print(k, v)
                    else:
                        if playerID in v:
                            print('This player is not a mafia!')
                            return 'you fucked up :)', None
                        if v[0] is not playerID and v[1]:
                            targetList.append(v[0])
                            print(k, v)
            fTargetList = ''
            count = 1
            # pprint(targetList)
            for _, item in enumerate(targetList):  # fix later
                fTargetList += f'\n{count}. <@{self.bot.get_user(item).id}>'
                count += 1
            embed = discord.Embed(
                title=f'**{settings.roleEmbedTitles["mafia"]}**', description=f'Type the number corresponding to the person\'s name to kill them.{fTargetList}')
            if type(playerID) is int:
                lastMsgAsList = await self.bot.get_user(playerID).history(limit=1).flatten()
            else:
                lastMsgAsList = await self.bot.get_user(playerID[0]).history(limit=1).flatten()
            lastMsg = lastMsgAsList[0]

            def allowedToSendEmbed(l, m):
                if l.author.id == self.bot.user.id and len(l.embeds) != 0:
                    return False
                else:
                    return not m

            if allowedToSendEmbed(lastMsgAsList[0], msgAlreadySent):
                msgAlreadySent = True
                lastMsg = await self.bot.get_user(playerID).send(content=None, embed=embed)
            if type(playerID) is int:
                lastMsgAsList = await self.bot.get_user(playerID).history(limit=1).flatten()
            else:
                lastMsgAsList = await self.bot.get_user(playerID[0]).history(limit=1).flatten()
            if lastMsgAsList[0] is not None:
                userIDToKill = 0
                validNumber = False  # USE GATHER
                while not validNumber:
                    # print(f'<@{lastMsg[0].author.id}>')
                    # msgSent = await self.bot.wait_for('message', check=lambda x: check(x, len(targetList), lastMsgAsList[0]))
                    msgSent = await self.waitForAction('kill', (None, playerID))
                    try:
                        userIDToKill = targetList[int(msgSent.content)-1]
                        # await msgSent.reply(f'<@{userIDToKill}> will be killed.')
                        # print('valid # received')
                        validNumber = True
                    except IndexError as e:
                        print(e)
                        await msgSent.reply(f'That number is out of range!')
                return await self.killPlayer(userIDToKill, None, 'mafia'), userIDToKill

        async def execMafias(self, playerID, targetDict):
            pass  # main diff will be that it gets sent to a mafia channel not DMs

        async def execDoctor(self, playerID, targetDict):
            pass

        async def execDetective(self, playerID, targetDict):
            pass

        execDict = {
            'mafia': execMafia,
            'doctor': execDoctor,
            'detective': execDetective
        }

        responseDict = {  # detective investigations are not announced
            'mafia': [None, None],
            'doctor': [None, None]
        }

        with open(f'games/{self.ctx.guild.id}.json', 'r') as guildFile:
            guildDict = json.loads(guildFile.read())
            guildFile.close()
        # embed + edit instead of send later
        await self.ctx.send('Messaging players...')
        # pprint(guildDict)
        # k, v = 'rolename', [ID/None, True/False]
        for k, v in guildDict['roles'].items():
            # await self.ctx.send(f'{k} is <@{v[0]}>')
            #print(f'V IS {v}')
            #print(k, v)
            if k != 'villager':
                if type(v[0]) is list:
                    playerIDList = v[0]
                else:  # if it's a list of ints and not a list of lists of ints
                    playerIDList = v
                if playerIDList[1]:  # if alive
                    if playerIDList[0] is None:
                        print('Problem in execNight: userID is None')
                    else:
                        if k in ('mafia', 'doctor'):
                            # use message only for mafia
                            responseDict[k] = await execDict[k](self, playerIDList[0], guildDict['roles'])
        nightUpdateEmbed = discord.Embed(
            title='Morning', description=responseDict['mafia'][0])  # returns msg, user
        await self.ctx.send(embed=nightUpdateEmbed)
        msgAlreadySent = True

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
            guildFile.close()
        return guildDict['players'][0]

    async def run(self):
        self.gameInitialized = False
        for i in range(50):
            ownerID = await self.getGameOwnerID()
            dct = next(self.stageGen(i=i))
            if dct['name'] == 'roleAssignment':
                if not self.gameInitialized:
                    await self.initGame()
            elif dct['name'].startswith('Day'):
                await self.execDay(dct)
                await self.bot.get_user(179757579759648769).send(f'day time {i} over')
            elif dct['name'].startswith('Night'):
                await self.execNight(dct)
                await self.bot.get_user(179757579759648769).send(f'night time {i} over')
