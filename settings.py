from discord import Embed
from datetime import datetime
import random
import string

minPlayers = 4
smallRulesetLimit = 7

# villager should be 0 by default
defaultRules = {  # groups of 5-7
    'mafia': 1,
    'doctor': 1,
    'detective': 1,
    'villager': 0
}

largeRules = {  # groups of 8 and up
    'mafia': 2,
    'doctor': 1,
    'detective': 1,
    'villager': 0
}

defaultMetadata = {
    'villageChannel': None,
    'graveyardChannel': None,
    'mafiaChannel': None,
    'aliveRole': None,
    'deadRole': None
}

defaultRoles = {
    'mafia': [[None, True]],  # 2nd bool = are they alive?
    'doctor': [[None, True]],
    'detective': [[None, True]],
    'villager': [[None, True]]
}

defaultGameData = {
    'docHealedSelf': False
}

deathMsgs = ('**PLAYER_NAME** was bludgeoned to death with a hammer.', '**PLAYER_NAME** was thrown into a shark tank.',
             '**PLAYER_NAME**\'s head was found rolling around in the **GUILD_NAME** town square.', '**PLAYER_NAME** was strangled with an extension cord.')
voteMsgs = ('**PLAYER_NAME** was sentenced to death by their fellow villagers.',
            '**PLAYER_NAME** was put under the guillotine.')

roleEmbedTitles = {
    'mafia': 'Who do you want to kill?',
    'doctor': 'Who do you want to heal?',
    'detective': 'Who do you want to investigate?'
}

helpInfo = {
    'report': 'Report a bug or problem'
}


def getLogID(length=8):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

def log(guildID, channelID, userID, action='Unknown Action', error=None):
    with open('discord.log', 'a') as logFile:
        logID = getLogID()
        if not error:
            logFile.write(logStr := f'\nAction {logID} @{guildID}/{channelID} called by {userID}: {action}')
        else:
            logFile.write(logStr := f'\nError {logID} @{guildID}/{channelID} called by {userID}: {error} caused by {action}')
    print(logStr.replace('\n', ''))
    return logID
