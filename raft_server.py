'''
Will implement the Raft protocol.
'''

from xmlrpc.server import SimpleXMLRPCServer
#from xmlrpc.server import SimpleXMLRPCServerHandler

class RaftNode():
    """docstring for RaftNode."""

    '''These will need to be persisted'''
    '''Put them into a State class which can handle the persistence'''
    currentTerm = 0
    votedFor = 0
    serverId = 1
    nextIndex = 1

    commitIndex = 0
    lastApplied = 0

    server = SimpleXMLRPCServer(('localhost', 8000))
    server.register_introspection_functions()

    def __init__(self, arg):
        # super(RaftNode, self).__init__()
        self.arg = arg

    def RequestVote(term, candidateId, lastLogIndex, lastLogTerm):
        print("RequestVote")
        return {currentTerm, true}

    server.register_function(RequestVote)

    def AppendEntries(term, leaderId, prevLogIndex, prevLogTerm,
                        entries, leaderCommit):
        # ignore requests from past terms
        if term < currentTerm:
            return (currentTerm, False)

        if prevLogIndex != 0:
            # get log entry at prevLogIndex
            (status, eTerm, _) = log.get_entry(prevLogIndex)
            if !status:
                return(currentTerm, False)
            if eTerm != prevLogTerm:
                return(currentTerm, False)
            newIndex = prevLogIndex

            (status, eTerm, _) = log.get_entry(newIndex)
            if status and (term != eTerm):
                # delete entry and all following

            # append entries
        else:
            # don't know yet
            
        currentTerm = term

        print("AppendEntries")
        print('term: ' + str(term))
        print('leaderId: ' + str(leaderId))
        print('prevLogIndex: ' + str(prevLogIndex))
        print('prevLogTerm: ' + str(prevLogTerm))
        print('entries: ' + str(entries))
        print('leaderCommit: ' + str(leaderCommit))
        return (currentTerm, True)

    server.register_function(AppendEntries)

    def adder_function(x, y):
        return x+y

    server.register_function(adder_function, 'add')

    def serve_forever(self):
        self.server.serve_forever()

    def hello(self):
        print("RaftNode: Hello " + self.arg)

if __name__ == '__main__':
    raftNode = RaftNode("Ken")
    raftNode.serve_forever()
    print("__main__: Goodbye World!")
