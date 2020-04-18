'''
Will implement the Raft protocol.
'''
import sys
import random
import queue
import time
import multiprocessing as mp
from xmlrpc.server import SimpleXMLRPCServer

#from xmlrpc.server import SimpleXMLRPCServerHandler
from server_state import *
from server_state import PersistedState

MIN_TIMEOUT = .3
MAX_TIMEOUT = .6

# server_id = 0
# persisted_state = 0
# log = 0
class RaftNode():
    def __init__(self, server_count, server_id, queues):
        print('RaftNode init', server_count, server_id)
        self.server_count = server_count
        self.server_id = server_id
        self.queues = queues
        self.in_q = queues[server_id]
        self.p_state = PersistedState(server_id)
        current_state = self.p_state.get_state()
        self.current_term = current_state['current_term']
        self.voted_for = current_state['voted_for']

        self.role = FOLLOWER
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = []
        self.match_index = []
        self.stopped = False
        #self.current_request = None
        self.leader = None
        self.sm = ServerMethods(self.p_state)

    def run(self):
        print('server %d started running' % self.server_id)
        while not self.stopped:
            request = {}
            timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
            try:
                request = self.in_q.get(True, timeout)
                print('server %d got request:' % self.server_id, request)
                operation = request['operation']
                if operation == 'stop':
                    self.stopped = True
                else:
                    print('ERROR: operation %s not implemented' % operation)
            except queue.Empty:
                # print('Server %d timed out' % self.server_id)
                pass    # Just ignore it for now
            except KeyboardInterrupt:
                print('Queue processing got keyboard interrupt')
                self.stopped = True

        print('server %d stopped running' % self.server_id)

    def issue_vote_request(self):
        self.role = CANDIDATE
        self.current_term += 1
        p_state.set_state({'current_term': self.current_term})
        request = {
            'operation': 'request_vote',
            'candidate_id': self.server_if,
            'current_term': self.current_term,
            }

class RaftClient(SimpleXMLRPCServer):
    def __init__(self, server_count, queues):
        self.port = 8099
        super().__init__(('localhost', self.port))

        self.server_count = server_count
        self.queues = queues
        self.leader = None
        self.shuttingdown = False

        self.register_introspection_functions()
        self.register_instance(ClientMethods(self, self.queues))

    def run(self):
        while not self.shuttingdown:
            self.handle_request()

    def shutdown(self):
        self.shuttingdown = True


class ClientMethods():
    def __init__(self, client, queues):
        self.client = client
        self.queues = queues

    def shutdown(self):

        print('stop_nodes')
        request = {'operation': 'stop'}
        for q in self.queues:
            q.put(request)

        print('stop server proxy')
        client.shutdown()

        return True

    def get_status(self, status):
        print('get_status')
        print('Current status: ', status)
        return status

    def list_methods(self):
        return ['get_status', 'shutdown', 'get_status']

def start_server(server_count, server_id, queues):
    print ('start_server', server_count, server_id)
    node = RaftNode(server_count, server_id, queues)
    node.run()

class ServerMethods():
    def __init__(self, p_state):
        self.p_state = p_state

    def request_vote(request):
        # term, candidate_id, last_log_index, last_log_term):
        print('Vote Requested', request)
        state = p_state.get_state()
        return {state['current_term'], True}
        return True

    def list_methods(self):
        return ['request_vote']


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
    print('main entry')
    # Get server id
    if len(sys.argv) < 2:
        print('Must supply server count')
        exit()

    server_count = int(sys.argv[1])
    if server_count < 1:
        print('Must have at least 1 server')
        exit()

    queues = []
    for i in range(server_count):
        queues.append(mp.Queue())

    processes = []
    for id in range(server_count):
        processes.append(mp.Process(target=start_server, args=(server_count, id, queues)))

    for p in processes:
        p.start()

    # The clien.run() will complete when the client recieves shutdown RPC
    client = RaftClient(server_count, queues)

    try:
        client.run()
    except KeyboardInterrupt:
        print('Keyboard Interupt, exitting')

    for q in queues:
        q.close()
        q.join_thread()

    for p in processes:
        p.join()
