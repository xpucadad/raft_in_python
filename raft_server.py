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

MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

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

        # retrieve persistent state
        self.p_state = PersistedState(server_id)
        current_state = self.p_state.get_state()
        self.current_term = current_state['current_term']
        self.voted_for = current_state['voted_for']

        # initialize non-persistent state
        self.role = FOLLOWER
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = []
        self.match_index = []
        self.stopped = False
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
            except queue.Empty:
                print('timeout in server %d' % self.server_id)
                # Do onthing for now
                continue
            except KeyboardInterrupt:
                print('Queue processing got keyboard interrupt')
                self.stopped = True
                continue

            # We have a request
            # Parse out the operation
            operation = request['operation']
            from_id = request['from']
    
            # process the operation
            response = {
                'operation': operation,
                'from': self.server_id,
                'to': from_id
                }

            # Verify that the message is for us; i
            if self.server_id != request['to']:
                error = 'server {} received message for {}; ignoring. request {}'.format(
                    self.server_id, request['to'], request)
                print(error)
                response['status'] = False
                response['error'] = error
                continue
 
            elif operation == 'stop':
                print('server %d got stop request' % self.server_id)
                self.stopped = True
                response['status'] = True

            else:
                error = 'ERROR: operation %s not implemented' % operation 
                print(error)
                response['status'] = False
                response['error'] = error

            print('server %d about to return response ' % self.server_id, response)
            self.queues[from_id].put(response)

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
    def __init__(self, server_count, client_id, queues):
        self.port = 8099
        super().__init__(('localhost', self.port))

        self.server_count = server_count
        self.client_id = client_id
        self.queues = queues
        self.leader = None
        self.shuttingdown = False

        self.register_introspection_functions()
        # We pass our self to ClientMethod calls to allow
        # the shutdown RPC to call our shutdown method.
        self.register_instance(
            ClientMethods(self, self.server_count, self.client_id, self.queues)
            )

    def run(self):
        while not self.shuttingdown:
            self.handle_request()

    def shutdown(self):
        print('client shutting down')
        self.shuttingdown = True


class ClientMethods():
    def __init__(self, client, server_count, client_id, queues):
        self.client = client
        self.server_count = server_count
        self.client_id = client_id
        self.queues = queues
        print('client id %e' % self.client_id)

    def shutdown(self):

        print('stop_nodes')
        request = {'operation': 'stop', 'from': self.client_id}
        # Our server_id is the same as SERVER_COUNT so the follwing
        # iteration will get every server but not this server.
        # self.server_id == SERVER_COUNT == len(queues
        # probably should pass in SERVER_COUNT explicitly in __init__.
        for id in range(self.server_count):
            request['to'] = id
            print('server %d sending stop operation to server %d' %
                (self.client_id, id), request)
            self.queues[id].put(request)

        # Get all the responses
        pending_responses = self.server_count
        print('client waiting for %d responses' % pending_responses)
        while pending_responses:
            timeout = random.randint(MIN_TIMEOUT, MAX_TIMEOUT)
            try:
                response = self.queues[self.client_id].get(True, timeout)
            except queue.Empty:
                print('client timed out waiting for stop responses')
                continue
            print('client got response', response)
            pending_responses -= 1

        print('stop server proxy')
        self.client.shutdown()

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
    ''' This code only runs on the main process and not on subprocesses '''
    print('main entry')
    # Get server id and verify that it's at least 1
    if len(sys.argv) < 2:
        print('Must supply server count')
        exit()

    server_count = int(sys.argv[1])
    if server_count < 1:
        print('Must have at least 1 server')
        exit()

    # Create the queues that the usbprocesses use to communicate,
    # plus one for the RPC client to use
    queues = []
    for i in range(server_count+1):
        queues.append(mp.Queue())

    # Create the sub processes, Note that the subprocesses won't execute the 
    # code hene, but will start with a call to start_server.
    #
    # Pass all the queues to the start_server function so that all processes
    # have access to them.
    processes = []
    for id in range(server_count):
        processes.append(mp.Process(target=start_server, args=(server_count, id, queues)))

    for p in processes:
        p.start()

    # The client implements an XML RPC server which another python script
    # can use to initiate events. The other process is the client refered
    # to in the raft documentation - i.e. the process that make requests
    # to charge the state machine.
    #
    # The clien.run() will complete when the client recieves shutdown RPC
    client_id = server_count
    client = RaftClient(server_count, client_id, queues)

    # To shotdown the servers, the client process should issue a shutdown 
    # RPC. This will cause the shotdown method of ClientMethods to get 
    # called which will send a shutdown operation to all subproceess
    # (using the queues) and then shutting down the XML RPC server itself.
    try:
        client.run()
    except KeyboardInterrupt:
        print('Keyboard Interupt, exitting')

    # Clean up the queues and processes before exitting
    for q in queues:
        q.close()
        q.join_thread()

    for p in processes:
        p.join()
