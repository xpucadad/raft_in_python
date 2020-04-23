import sys
import xmlrpc.client

def main():

    s = xmlrpc.client.ServerProxy('http://localhost:8099')

    #term, leaderId, prevLogIndex, prevLogTerm,
    #                    entries, leaderCommit
    print(s.system.listMethods())

    print('client result from shutdown:', s.shutdown())

if __name__ == '__main__':
    main()
