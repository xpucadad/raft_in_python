'''
Will implement the Raft protocol.
'''

from xmlrpc.server import SimpleXMLRPCServer
#from xmlrpc.server import SimpleXMLRPCServerHandler
from server_states import *

server_id = 1
raft_server = RaftServer(server_id)
server = SimpleXMLRPCServer(('localhost', 8000 + server_id))
server.register_introspection_functions()
server.register_function(AppendEntries)
server.register_function(RequestVote)
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nKeyboard interupt recieved; exitting")


def RequestVote(term, candidate_id, last_log_index, last_log_term):
    print("RequestVote")
    return {self.current_term, true}


def AppendEntries(term, leader_id, prev_log_index, prev_log_term,
                    entries, leader_commit):
    server_state = raft_server.server_state

    print("Server state: " + server_names[server_state])
    print("AppendEntries")
    print('term: ' + str(term))
    print('leader_id: ' + str(leader_id))
    print('prev_log_index: ' + str(prev_log_index))
    print('prev_log_term: ' + str(prev_log_term))
    print('entries: ' + str(entries))
    print('leaderCommit: ' + str(leader_commit))

    if server_state != FOLLOWER:
        status = False

    if raft_server.server_stane == FOLLOWER:
        raft_server.current_term = term
        status = True

    return (raft_server.current_term, status)


class RaftServer():

    def __init__(self, server_id):
        '''Need to be persisted'''
        self.server_id = server_id
        self.server_state = Follower
        self.current_term = 0
        self.voted_for = 0
        self.next_index = 1

        self.commit_index = 0
        self.last_applied = 0
