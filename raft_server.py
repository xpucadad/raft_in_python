'''
Will implement the Raft protocol.
'''

from xmlrpc.server import SimpleXMLRPCServer
#from xmlrpc.server import SimpleXMLRPCServerHandler
from server_states import *

def main(server_id):
    raft_server = RaftServer(server_id)

def RequestVote(term, candidate_id, last_log_index, last_log_term):
    print("RequestVote")
    return {self.current_term, true}

server.register_function(RequestVote)

def AppendEntries(term, leader_id, prev_log_index, prev_log_term,
                    entries, leader_commit):
    # ignore requests from past terms
    if term < self.current_term:
        return (self.current_term, False)

    if prev_log_index != 0:
        # get log entry at prev_log_index
        (status, e_term, _) = log.get_entry(prev_log_index)
        if not status:
            return(self.current_term, False)

        if e_term != prev_log_term:
            return(self.current_term, False)

        new_index = prev_log_index

        (status, e_term, _) = log.get_entry(new_index)
        if status and (term != e_term):
            # delete entry and all following
            Pass
        # append entries
        else:
        # don't know yet
            Pass

    self.current_term = term

    print("AppendEntries")
    print('term: ' + str(term))
    print('leader_id: ' + str(leader_id))
    print('prev_log_index: ' + str(prev_log_index))
    print('prev_log_term: ' + str(prev_log_term))
    print('entries: ' + str(entries))
    print('leaderCommit: ' + str(leader_commit))
    return (self.current_term, True)

server.register_function(AppendEntries)

class RaftServer():
    """docstring for RaftServer."""
    server_state = FOLLOWER

    '''These will need to be persisted'''
    '''Put them into a State class which can handle the persistence'''
    current_term = 0
    voted_for = 0
    server_id = 1
    next_index = 1

    commit_index = 0
    last_applied = 0

    server = SimpleXMLRPCServer(('localhost', 8000 + server_id))
    server.register_introspection_functions()

    def __init__(self, server_id):
        # super(RaftNode, self).__init__()
        self.server_id = server_id

    def serve_forever(self):
        self.server.serve_forever()

if __name__ == '__main__':
    raft_server = RaftServer("Ken")
    try:
        raft_server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interupt recieved; exitting")

    print("__main__: Goodbye World!")
