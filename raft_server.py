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

        self.server_role = FOLLOWER
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = []
        self.match_index = []
        self.stopped = False
        #self.current_request = None
        self.leader = None

    def run(self):
        print('server %d started running' % self.server_id)
        while not self.stopped:
            request = {}
            timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
            try:
                request = self.in_q.get(True, timeout)
                print('server %d got request:' % self.server_id, request)
                if request['operation'] == 'Stop':
                    self.stopped = True
                else:
                    self.handle_request(self.current_request)
            except queue.Empty:
                #print('server %d queue empty' % self.server_id)
                pass
            # except KeyboardInterrupt:
            #     print('server %d got keyboard interupt' % self.server_id)
            #     self.stopped = True


        print('server %d stopped running' % self.server_id)

    def handle_request(self, request):
        print('server %d got request' % self.server_id, request)
        # parse
        # handle
        # respond

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

    def _dispatch(self, method, params):
        print('dispatch', method, params)

        result = None
        if method == 'get_status':
            result = self.get_status(*params)
        elif method == 'shutdown':
            result = self.shutdown()
        else:
            print('ERROR!!')
        return result

    def shutdown(self):

        print('stop_nodes')
        request = {'operation': 'Stop'}
        for q in self.queues:
            q.put(request)

        print('stop server proxy')
        client.shutdown()

        return True

    def get_status(self, status):
        print('get_status')
        print('Current status: ', status)
        return status

def start_server(server_count, server_id, queues):
    print ('start_server', server_count, server_id)
    node = RaftNode(server_count, server_id, queues)
    node.run()

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
    print('main entry')
    # Get server id
    if len(sys.argv) < 2:
        print('Must supply server count')
        exit()

    server_count = int(sys.argv[1])

    queues = []
    for i in range(server_count):
        queues.append(mp.Queue())

    processes = []
    for id in range(server_count):
        processes.append(mp.Process(target=start_server, args=(server_count, id, queues)))

    for p in processes:
        p.start()

    client = RaftClient(server_count, queues)
    client.run()

    for q in queues:
        q.close()
        q.join_thread()

    for p in processes:
        p.join()
