import urllib2


def callbackdata(data):
    return data

sheetId = "1xCvYdmH13sQg41dOZfgAiYZLI1JzmML7IhTW7QzNktg"
userName = "bob"

url = "http://spreadsheets.google.com/tq?tqx=responseHandler:callbackdata&key=" + sheetId + "&sheet=" + userName

rawResponse = urllib2.urlopen(url).read()
response = rawResponse.splitlines()[1].replace(';','').replace('null','{}').replace('true','"true"')
responseDict = eval(response)
ChannelRow = responseDict["table"]['rows'][1]['c'];
dummy = 5