'''
Will implement the Raft protocol.
'''
import sys
import random

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy

#from xmlrpc.server import SimpleXMLRPCServerHandler
from server_state import *
from server_state import PersistedState

MIN_TIMEOUT = .3
MAX_TIMEOUT = .6

# server_id = 0
# persisted_state = 0
# log = 0
class RaftNode(SimpleXMLRPCServer):
    def __init__(self, server_count, server_id):
        self.server_count = server_count
        self.server_id = server_id
        self.port = 8000 + server_id
        super().__init__(('localhost', self.port))
        self.register_introspection_functions()
        self.p_state = PersistedState(server_id)
        current_state = self.p_state.get_state()
        self.current_term = current_state['current_term']
        self.voted_for = current_state['voted_for']

        self.server_role = FOLLOWER
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = []
        self.match_index = []

        self.register_introspection_functions()
        self.register_function(StupidFunction)
        self.register_function(RequestVote)
        # self.register_function(AppendEntries)

        # Setup proxies for each of the servers
        self.proxies = [
            ServerProxy('http://localhost:800' + str(i)) for i in range(5)
            ]

        print ('proxies', self.proxies)

    def handle_timeout(self):
        # print('Got a timeout!')
        pass

    def run(self):
        while True:
            # The timeout will call handle_timeout when
            # the handle_request times out.
            self.timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
            # print('setting timeout of %f' % self.timeout)
            self.handle_request()

def main(server_count, server_id):
    server = RaftNode(server_count, server_id)

    try:
        server.run()
    except KeyboardInterrupt:
        print("\nKeyboard interupt recieved; exitting")

def StupidFunction(message):
    print(message)
    return message

def RequestVote(term, candidate_id, last_log_index, last_log_term):
    print("RequestVote")
    p_state = persisted_state.get_state(server_id)

    # Do voting here

    return {p_state['current_term'], true}

def AppendEntries(term, leader_id, prev_log_index, prev_log_term,
                    entries, leader_commit):
    print("AppendEntries")
    print('term: ' + str(term))
    print('leader_id: ' + str(leader_id))
    print('prev_log_index: ' + str(prev_log_index))
    print('prev_log_term: ' + str(prev_log_term))
    print('entries: ' + str(entries))
    print('leaderCommit: ' + str(leader_commit))

    p_state = persisted_state.get_state()
    current_term = p_state['current_term']
    print('current_term: ' + str(current_term))
    print('voted_for: ' + str(p_state['voted_for']))

    if term < current_term:
        return (current_term, False)

    (status, entry_term, _) = log.get_entry(prev_log_index)
    if not status:
        return(current_term, False)

    if entry_term != prev_log_term:
        return(current_term, False)

    (status, entry_term, _) = log.get_entry(prev_log_index)
    if status and (term != entry_term):
        # delete entry and all following
        Pass
    # append entries
    else:
    # don't know yet
        Pass

    p_state['current_term'] = term
    persisted_state.set_state(p_state)

    return (term, True)

if __name__ == '__main__':
    # Get server id
    if len(sys.argv) < 3:
        print('Must supply server count and server id')
        exit()

    server_count = int(sys.argv[1])
    server_id = int(sys.argv[2])
    main(server_count, server_id)
