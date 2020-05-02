'''
Will implement the Raft protocol.
'''
import sys
import random
import queue
import time
import multiprocessing as mp
from xmlrpc.server import SimpleXMLRPCServer
from threading import Thread

#from xmlrpc.server import SimpleXMLRPCServerHandler
from node_state import *
from node_state import PersistedState

MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

# node_id = 0
# persisted_state = 0
# log = 0

'''
    This class's run method consumes entries from the other Raft
    Nodes via their pipes.
'''
class RaftNode():
    def __init__(self, node_count, node_id, pipes):
        print('RaftNode init', node_count, node_id)
        self.node_count = node_count
        self.node_id = node_id
        self.pipes = pipes
        self.connection = pipes[node_id].server_side

        # PersistedState provides access to any persistent state.
        # Persisted state is stored in Mongo database.
        self.persisted_state = PersistedState(node_id)
        # current_state = self.persisted_state.get_state()
        # self.current_term = current_state['current_term']
        # self.voted_for = current_state['voted_for']

        # initialize non-persistent state
        self.role = FOLLOWER
        self.last_log_index = 0
        self.last_log_term = 0
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = []
        self.match_index = []
        self.stopped = False
        self.leader = None

        # The ServerMethods class contains the remote procedures that
        # might get called by other Raft nodes.
        self.node_methods = RaftNodeMethods(self, self.persisted_state)

 
    def run(self):
        print('node %d started running' % self.node_id)

        # Main loop for consuming incoming requests
        while not self.stopped:
            request = {}
            timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)

            have_request = self.connection.poll(timeout)
            if not have_request:
                # If there is no message, assume the leader is dead
                # and run for leader
                print('node %d timed out waiting for a request' % self.node_id )
                if self.role == FOLLOWER:
                    self._run_for_leader()
                elif self.role = CANDIDATE:
                    self.role = FOLLOWER
                continue
            else:
                # Process a request
                request = self.connection.recv()
                print('node %d got request:' % self.node_id, request)

            # We have a request
            # Parse out the operation
            operation = request['operation']
            source_id = request['from']
    
            # prepare response
            response = {
                'type': 'response',
                'operation': operation,
                'from': self.node_id,
                'to': source_id
                }

            # Verify that the message is for us
            if self.node_id != request['to']:
                error = 'node {} received message for {}; ignoring. request {}'.format(
                    self.node_id, request['to'], request)
                print(error)
                response['status'] = False
                response['error'] = error
            else:
                (response['status'], response['return_args']) =
                    self.node_methods.run_method(operation, request)

            print('node %d about to return response ' 
                        % self.node_id, response)
            self.connection.send(response)

        print('node %d stopped running' % self.node_id)

    # Would it make more sense for this to be in ServerMethods? It's
    # not really callable from anywhere but this class, so for now
    # I'll leave it here
    def _run_for_leader(self):
        self.role = CANDIDATE
        new_term = self.persisted_state.get_current_term() + 1
        self.persisted_state.set_current_term = new_term
        self.persisted_state.set_voted_for = self.node_id
 
        request = {
            'from': self.node_id,
            'operation': 'request_vote'
            'term': new_term,
            'candiidate_id': self.node_id,
            'last_log_index': self.last_log_index,
            'last_log_term': self.last_log_term
        }

        statuses = [None] * self.node_count
        except_list = [self.node_id]
        statuses = broadcast_request(self.pipes, request, except_list)
        statuses[self.node_id] = True

 
    def stop(self):
        self.stopped = True
        return True

class RaftNodeMethods():
    def __init__(self, my_node, persistent_state):
        self.my_node = my_node
        self.persistent_state = persistent_state
        self.registered_methods = {}
        self.registered_methods['stop'] = self.stop
 
    def call_method(self, operation, request):
        # methods are passed an argument dict containing whatever
        # data they require (passed from the source Raft node in the
        # incoming request)
        # methods must return a status of True or False, plus a dict
        # contained any data that it needs to return
        # The run_method method will then package this in a dict with 2
        # entries, 'status' for the True/False value, and 'output' for 
        # the data in the returned output dict.
        method = self.registered_methods[operation]
        if method:
            result = method(request)
        else:
            error = 'No such method' + operation
            result = (False, {'error': error} )

        return result


    def stop(self, args):
        status = self.my_node.stop()
        return (True, {})

    def request_vote(self, args):
        return (True, {})


    def append_entries(self, args):
        return (True, {})


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
    def __init__(self, node_count, client_id, pipes):
        print('RaftClient %d' % client_id)

        # Call our parent to init the socket
        self.port = 8099
        super().__init__(('localhost', self.port))

        self.node_count = node_count
        self.client_id = client_id
        self.pipes = pipes

        self.leader = None
        self.shuttingdown = False

        self.register_introspection_functions()
        # We pass our self to ClientMethod calls to allow
        # the shutdown RPC to call our shutdown method.
        self.register_instance(
            ClientMethods(self, self.node_count, self.client_id, self.pipes))
    

    def run(self):
        print('RaftClient started running')
        while not self.shuttingdown:
            self.handle_request()

    def shutdown(self):
        print('Raft client shutting down')
        self.shuttingdown = True
        return True

class NodeCommunicationController():
    def __init__(self, node_count, from_id, pipes)
        self.node_count = node_count
        self.from_id = from_id
        self.pipes = pipes

    def broadcast_request(self, request, exclude=[]):
        self.request = request
        self.operation = self.request['operation']
        statuses = [None] * self.node_count
        return_args = [None] * self.node_count
        full_responses = [None] * self.node_count

        self.request['type'] = 'request'

        threads = [None] * self.node_count
        for nid in range(self.node_count):
            if nid in exclude:
                print('broadcast excluding node %d' % nid)
                continue

            self.request['to'] = nid
            connection = self.pipes[nid].client_side

            thread = DoRequest(connection, dict(self.request))
            threads[nid] = thread
            thread.start()

        for tid in range(len(threads)):
            thread = threads[tid]
            if not thread:
                continue

            full_response = {
                'type': 'response',
                'operation': self.operation,
                'to': self.from_id,
                'from': tid
            }
            thread.join()
            result = thread.get_results()
            status = result[0]
            ra = result[1]
            statuses[tid] = status
            return_args[tid] = ra
            full_response.update({
                'status': status,
                'return_args': ra
                })
            full_responses[tid] = full_response

        return (statuses, return_args, full_responses)


class ClientMethods():
    def __init__(self, client, node_count, client_id, pipes):
        
        print('Client Methods %d' % client_id)
        self.client = client    # This is the instance of RaftClient that
                                # created this instance of ClientMethods
        self.node_count = node_count
        self.client_id = client_id
        self.pipes = pipes
        self.leader = 0     # assume leader is 0

        self.ncc = NodeCommunicationController(self.node_count, self.cilent_node, self.pipes)

    
    def shutdown(self):
        print('client requested a stop')
        request = {'type': 'request', 'operation': 'stop', 'from': self.client_id}
        # Our node_id is the same as node_COUNT so the follwing
        # iteration will get every server but not this server.
        # self.node_id == SERVER_COUNT == len(queues
        # probably should pass in SERVER_COUNT explicitly in __init__.
        statuses = self.ncc.broadcast_request(request, [])

        print('ClientMethods results from shutdown request: ', statuses)
        print('stop server proxy')
        self.client.shutdown()

        return True

    def list_methods(self):
        return ['shutdown']

'''
This thread sends a request to one server and then processes the 
returned value
'''

class DoRequest(Thread):
    def __init__(self, connection, request):
        Thread.__init__(self)
        self.connection = connection
        self.request = request
        self.to = self.request['to']
        self.result = None

    def run(self):
        self.connection.send(self.request)

        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)

        if self.connection.poll(timeout):
            reply = self.connection.recv()
            self.rstatus = reply['status']
            self.return_args = reply['return_args']
        else:
            self.status = False
            self.return_args = {}

    def get_results(self):
        return (self.status, self.return_args)

# def broadcast_request(pipes, request, except_list):
#     node_count = len(pipes) - 1
#     statuses = [False] * node_count

#     threads = []
#     for i in range(node_count):
#         if i in except_list:
#             continue
#         thread = DoRequest(i, pipes[i].client_side, request)
#         threads.append(thread)
#         thread.start()

#     for thread in threads:
#         thread.join()
#         result = thread.get_result()
#         statuses[result['from']] = result['status']

#     return statuses

''' This is the top level entry point for all subprocesses '''
def start_node(node_count, node_id, connection):
    print ('start_node', node_count, node_id)

    # Create and run the class which will consume entries on the queue
    # request_queues[node_id].
    node = RaftNode(node_count, node_id, connection)
    try:
        node.run()
    except KeyboardInterrupt:
        print('node got keyboard interrupt; exitting')



# def AppendEntries(term, leader_id, prev_log_index, prev_log_term,
#                     entries, leader_commit):
#     print("AppendEntries")
#     print('term: ' + str(term))
#     print('leader_id: ' + str(leader_id))
#     print('prev_log_index: ' + str(prev_log_index))
#     print('prev_log_term: ' + str(prev_log_term))
#     print('entries: ' + str(entries))
#     print('leaderCommit: ' + str(leader_commit))

#     p_state = persisted_state.get_state()
#     current_term = p_state['current_term']
#     print('current_term: ' + str(current_term))
#     print('voted_for: ' + str(p_state['voted_for']))

#     if term < current_term:
#         return (current_term, False)

#     (status, entry_term, _) = log.get_entry(prev_log_index)
#     if not status:
#         return(current_term, False)

#     if entry_term != prev_log_term:
#         return(current_term, False)

#     (status, entry_term, _) = log.get_entry(prev_log_index)
#     if status and (term != entry_term):
#         # delete entry and all following
#         Pass
#     # append entries
#     else:
#     # don't know yet
#         Pass

#     p_state['current_term'] = term
#     persisted_state.set_state(p_state)

#     return (term, True)

class RaftPipe():
    def __init__(self):
        (self.client_side, self.server_side) = mp.Pipe()

    def close(self):
        self.client_side.close()
        self.server_side.close()

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

    node_count = int(sys.argv[1])
    if node_count < 1:
        print('Must have at least 1 server')
        exit()

    # Create the pipes
    pipes = [None] * (node_count + 1)
    for i in range(node_count + 1):
        pipes[i] = RaftPipe()

    # Create the sub processes, Note that the subprocesses won't execute the 
    # code hene, but will start with a call to start_server.
    #
    # Pass all the pipes to the start_server function so that all processes
    # have access to them.
    #
    # start_server is the function where all subprocesses start execution
    processes = [None] * node_count

    # Create all the subprocesses
    for nid in range(node_count):
        connection = pipes[nid].node_side
        processes[nid] = mp.Process(
            target=start_node, 
            args=(node_count, nid, connection)
            )

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
    client_id = node_count    # This is equivalent to the node_id and
                                # identives the queues used by this process
    client = RaftClient(node_count, client_id, pipes)

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
