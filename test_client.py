import sys
import xmlrpc.client

def main():

    s = xmlrpc.client.ServerProxy('http://localhost:8099')

    #term, leaderId, prevLogIndex, prevLogTerm,
    #                    entries, leaderCommit
    print(s.system.listMethods())

    for i in range(5):
        print(s.get_status(str(i)))

    s.shutdown()

    # Playing leader
    currentTerm = 1
    votedFor = 1

    commitIndex = 0
    lastApplied = 0

    nextIndex = [1, 1, 1]

    matchIndex = [0, 0, 0]


    # print(s.AppendEntries(currentTerm, server_id, lastApplied,
    #     currentTerm-1, ['one', 'two'], commitIndex))

if __name__ == '__main__':
    main()
