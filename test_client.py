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

if __name__ == '__main__':
    main()
