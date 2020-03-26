import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:8000')

#term, leaderId, prevLogIndex, prevLogTerm,
#                    entries, leaderCommit

print(s.AppendEntries(1,1,0,1,"entry",1))

print(s.add(5, 6))

print(s.system.listMethods())
