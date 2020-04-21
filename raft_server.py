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

def print_array(array):
    for index in range(len(array)):
        print(array[index])

# server_id = 0
# persisted_state = 0
# log = 0

'''
    This class's run method consumes entries from the 
    self.request_queues[self.server_id] queue
'''
class RaftNode():
    def __init__(self, server_count, server_id, pipes):
        print('RaftNode init', server_count, server_id)
        self.server_count = server_count
        self.server_id = server_id
        self.pipes = pipes

        # retrieve persistent state
        self.persisted_state = PersistedState(server_id)
        current_state = self.persisted_state.get_state()
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

 
    def run(self):
        print('server %d started running' % self.server_id)

        # Main loop for consuming incoming requests
        while not self.stopped:
            request = {}
            timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)

            in_conn = self.pipes[self.server_id].in_conn

            have_request = in_conn.poll(timeout)

            if not have_request:
                print('server %d timed out waiting for a request' % self.server_id )
                continue

            request = in_conn.recv()
            print('server %d got request:' % self.server_id, request)

            # We have a request
            # Parse out the operation
            operation = request['operation']
            from_id = request['from']
    
            # prepare response
            response = {
                'type': 'response',
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
 
            if operation == 'stop':
                response['status'] = self.stop()
 
            else:
                response['error'] = 'unrecognized node call %s; ingoring' % operation
                response['status'] = False


            result = self.server_methods.call_method(operation, request)
 
            print('server %d about to return response ' 
                        % self.server_id, response)
            out_conn = self.pipes[from_id].out_conn
            out_conn.send(response)

        print('server %d stopped running' % self.server_id)

    def stop(self):
        self.stopped = True
        return True

'''
    This class processes XMLRPC calls sent to 
    http://localhost:8099 for an external client (usually to 
    request a state change in the disptributed state machine.

    The requests are calls to methods in the ClientMethods class.
    these may be admin requests (such as a stop request), or calls
    from a client requesting a change to the distributed state 
    machine that the raft servers are here to process.
'''
class RaftClient(SimpleXMLRPCServer):
    def __init__(self, server_count, client_id, pipes):
        print('RaftClient %d' % client_id)

        # Call our parent to init the socket
        self.port = 8099
        super().__init__(('localhost', self.port))

        self.server_count = server_count
        self.client_id = client_id
        self.pipes = pipes

        self.leader = None
        self.shuttingdown = False

        self.register_introspection_functions()
        # We pass our self to ClientMethod calls to allow
        # the shutdown RPC to call our shutdown method.
        self.register_instance(
            ClientMethods(self, self.server_count, self.client_id, self.pipes))
    

    def run(self):
        print('RaftClient started running')
        while not self.shuttingdown:
            self.handle_request()

    def shutdown(self):
        print('client shutting down')
        self.shuttingdown = True


class ClientMethods():
    def __init__(self, client, server_count, client_id, pipes):
        
        print('Client Methods %d' % client_id)
        self.client = client    # This is the instance of RaftClient that
                                # created this instance of ClientMethods
        self.server_count = server_count
        self.client_id = client_id
        self.pipes = pipes
        self.leader = 0     # assume leader is 0

    
    def shutdown(self):
        print('client requested a stop')
        request = {'type': 'request', 'operation': 'stop', 'from': self.client_id}
        # Our server_id is the same as SERVER_COUNT so the follwing
        # iteration will get every server but not this server.
        # self.server_id == SERVER_COUNT == len(queues
        # probably should pass in SERVER_COUNT explicitly in __init__.
        for target_id in range(self.server_count):
            request['to'] = target_id
            out_conn = self.pipes[target_id].out_conn
            print('server %d sending stop operation to server %d' %
                (self.client_id, target_id), request)
            out_conn.send(request)

        # Get all the responses
        in_conn = self.pipes[self.client_id].in_conn
        pending_responses = self.server_count
        print('client waiting for %d responses' % pending_responses)
        while pending_responses:
            timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)

            have_response = in_conn.poll(timeout)
            if not have_response:
                print ('client %d timed out waiting for response' % self.client_id)
                continue

            else:
                response = in_conn.recv()
                print('client %d got response:' % self.client_id, response)
                
            pending_responses -= 1

        print('stop server proxy')
        self.client.shutdown()

        return True

    def broadcast(self, request, except_list):
        for target_id in range(self.server_count) and not in except_list:
            
    # dummy request for testing
    def get_status(self, status):
        print('get_status')
        print('Current status: ', status)
        return status

    def list_methods(self):
        return ['get_status', 'shutdown', 'get_status']

''' This is the top level entry point for all subprocesses '''
def start_server(server_count, server_id, pipes):
    print ('start_server', server_count, server_id)

    # Create and run the class which will consume entries on the queue
    # request_queues[server_id].
    node = RaftNode(server_count, server_id, pipes)
    node.run()



# class ServerMethods():
    # def __init__(self, p_state):
    #     self.p_state = p_state

    # def request_vote(request):
    #     # term, candidate_id, last_log_index, last_log_term):
    #     print('Vote Requested', request)
    #     state = p_state.get_state()
    #     return {state['current_term'], True}
    #     return True

    # def list_methods(self):
    #     return ['request_vote']


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

class RaftPipe():
    def __init__(self, in_conn, out_conn):
        self.in_conn = in_conn
        self.out_conn = out_conn

    def close(self):
        self.in_conn.close()
        self.out_conn.close()

'''
    The following code is only executed in the process where this
    script is executed, and not in any of the spawned subprocesses
'''
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

    # Create the pipes
    pipes = [None] * (server_count + 1)
    for i in range(server_count + 1):
        (in_conn, out_conn) = mp.Pipe()
        pipes[i] = RaftPipe(in_conn, out_conn)

    # Create the sub processes, Note that the subprocesses won't execute the 
    # code hene, but will start with a call to start_server.
    #
    # Pass all the pipes to the start_server function so that all processes
    # have access to them.
    #
    # start_server is the function where all subprocesses start execution
    processes = [None] * server_count

    # Create all the subprocesses
    for id in range(server_count):
        processes[id] = mp.Process(target=start_server, 
                args=(server_count, id, pipes))

    # Start all the subprocesses
    for p in processes:
        p.start()

    # The client implements an XML RPC server which another python script
    # can use to initiate events. The other process is the client refered
    # to in the raft documentation - i.e. the process that make requests
    # to charge the state machine.
    #
    # The clien.run() will complete when the client recieves shutdown RPC
    #
    # Note that this code is never run in any of the subprocesses, but only
    # here in the original process.
    client_id = server_count    # This is equivalent to the server_id and
                                # identives the queues used by this process
    client = RaftClient(server_count, client_id, pipes)

    # To shotdown the servers, the client process should issue a shutdown 
    # RPC. This will cause the shotdown method of ClientMethods to get 
    # called which will send a shutdown operation to all subproceess
    # (using the queues) and then shutting down the XML RPC server itself.
    try:
        client.run()
    except KeyboardInterrupt:
        print('Keyboard Interupt, exitting')

    # Clean up the queues and processes before exitting
    for p in pipes:
        p.close()

    for p in processes:
        p.join()
