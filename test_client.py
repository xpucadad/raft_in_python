import sys
import xmlrpc.client

def main(server_id):

    s = xmlrpc.client.ServerProxy('http://localhost:800' + str(server_id))

    #term, leaderId, prevLogIndex, prevLogTerm,
    #                    entries, leaderCommit
    print(s.system.listMethods())

    # Playing leader
    currentTerm = 1
    votedFor = 1

    commitIndex = 0
    lastApplied = 0

    nextIndex = [1, 1, 1]

    matchIndex = [0, 0, 0]


    print(s.AppendEntries(currentTerm, server_id, lastApplied,
        currentTerm-1, ['one', 'two'], commitIndex))

if __name__ == '__main__':
    # Get server id
    if len(sys.argv) < 2:
        print('Must supply server id')
        exit()

    server_id = int(sys.argv[1])
    main(server_id)
