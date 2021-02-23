from discord import Embed
minPlayers = 4
smallRulesetLimit = 7

#villager should be 0 by default
defaultRules = {  # groups of 5-7
    'mafia': 1,
    'doctor': 1,
    'detective': 1,
    'villager': 0
}

largeRules = {  # groups of 8 and up
    'mafia': 1,
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

roleEmbedTitles = {
    'mafia': 'Who do you want to kill?',
    'doctor': 'Who do you want to heal?',
    'detective': 'Who do you want to investigate?'
}

helpInfo = {
    'report': 'Report a bug or problem'
}