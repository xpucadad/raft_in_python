'''
Will implement the Raft protocol.
'''

from xmlrpc.server import SimpleXMLRPCServer
#from xmlrpc.server import SimpleXMLRPCServerHandler

class LogEntry():
    entry = ""
    def SetValue(self, value):
        self.value = value

class RaftNode():
    """docstring for RaftNode."""

    '''These will need to be persisted'''
    currentTerm = 0
    votedFor = 0
    log = []


    def __init__(self, arg):
        # super(RaftNode, self).__init__()
        self.arg = arg
        self.server = SimpleXMLRPCServer(('localhost', 8000))
        self.server.register_introspection_functions()

        def RequestVote(term, candidateId, lastLogIndex, lastLogTerm):
            print("RequestVote")
            return {currentTerm, true}
        self.server.register_function(RequestVote)

        def AppendEntries(term, leaderId, prevLogIndex, prevLogTerm,
                            entries, leaderCommit):
            print("AppendEntries")
            return {currentTerm, true}
        self.server.register_function(AppendEntries)

        def adder_function(x, y):
            return x+y
        self.server.register_function(adder_function, 'add')

    def serve_forever(self):
        self.server.serve_forever()

    def hello(self):
        print("RaftNode: Hello " + self.arg)

if __name__ == '__main__':
    raftNode = RaftNode("Ken")
    raftNode.serve_forever()
    print("__main__: Goodbye World!")
