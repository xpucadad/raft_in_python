import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:8000')

#term, leaderId, prevLogIndex, prevLogTerm,
#                    entries, leaderCommit

print(s.add(5, 6))

print(s.system.listMethods())
