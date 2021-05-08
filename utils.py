def csvToList(csvData):
    return str(csvData).split(',')


def listToCSV(csvList):
    return ','.join(csvList)


def repInt(string, bounds=None):
    try:
        num = int(string)
        return bounds[0] <= num <= bounds[1] if bounds else True
    except ValueError:
        return False


def validGameRulesCheck(mafia, doc, detective, total):
    print(mafia, doc, detective, total)
    villagers = total - (mafia + doc + detective)
    if any((mafia > total, mafia < 1, doc > total, doc < 0, detective > total, detective < 0, villagers > total, villagers < 1)):
        return False
    return True
    