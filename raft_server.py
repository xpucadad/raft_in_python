'''
Will implement the Raft protocol.
'''
import sys

from xmlrpc.server import SimpleXMLRPCServer
#from xmlrpc.server import SimpleXMLRPCServerHandler
from server_state import *
from server_state import PersistedState

from log import Log

server_id = 0
persisted_state = 0
log = 0

def main(p_server_id):
    global server_id
    global persisted_state
    global log
    server_id = p_server_id
    server = SimpleXMLRPCServer(('localhost', 8000 + server_id))
    server.register_introspection_functions()
    server.register_function(RequestVote)
    server.register_function(AppendEntries)

    role = FOLLOWER
    commit_index = 0
    last_applied = 0
    next_index = []
    match_index = []
    persisted_state = PersistedState(server_id)

    log = Log(server_id)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interupt recieved; exitting")

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
    if len(sys.argv) < 2:
        print('Must supply server id')
        exit()

    server_id = int(sys.argv[1])
    main(server_id)
