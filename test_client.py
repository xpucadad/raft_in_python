import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:8000')

#term, leaderId, prevLogIndex, prevLogTerm,
#                    entries, leaderCommit

print(s.add(5, 6))

print(s.system.listMethods())

# Playing leader
serverId = 1
currentTerm = 1
votedFor = 1

commitIndex = 0
lastApplied = 0

nextIndex = [1, 1, 1]

matchIndex = [0, 0, 0]


print(s.AppendEntries(currentTerm, serverId, lastApplied,
    currentTerm-1, ['one', 'two'], commitIndex))
