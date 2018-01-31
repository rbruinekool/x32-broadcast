import urllib2


def callbackdata(data):
    return data

sheetId = "1xCvYdmH13sQg41dOZfgAiYZLI1JzmML7IhTW7QzNktg"
userName = "bob"

url = "http://spreadsheets.google.com/tq?tqx=responseHandler:callbackdata&key=" + sheetId + "&sheet=" + userName

rawResponse = urllib2.urlopen(url).read()
response = rawResponse.splitlines()[1].replace(';','').replace('null','{}').replace('true','"true"')
responseDict = eval(response)
allRows = responseDict["table"]['rows'];

currentRow = []
channelDict = {}

for i in range(0, len(allRows)):
    for j in range(1, len(allRows[i]['c'])):
        if len(allRows[i]['c'][j].values()) > 0:
            if type(allRows[i]['c'][j].values()[0]) == str:
                currentRow.append(allRows[i]['c'][j].values()[0])
                try:
                    currentRow[j - 1] = int(currentRow[j - 1])
                except ValueError:
                    pass
        else:
            currentRow.append("")

    channelDict[allRows[i]['c'][0]['v']] = currentRow
    currentRow = []
dummy = 5