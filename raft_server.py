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
from server_state import *
from server_state import PersistedState

MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

# server_id = 0
# persisted_state = 0
# log = 0

'''
    This class's run method consumes entries from the other Raft
    Nodes via their pipes.
'''
class RaftNode():
    def __init__(self, server_count, server_id, pipes):
        print('RaftNode init', server_count, server_id)
        self.server_count = server_count
        self.server_id = server_id
        self.pipes = pipes
        self.connection = pipes[server_id].server_side

        # PersistedState provides access to any persistent state.
        # Persisted state is stored in Mongo database.
        self.persisted_state = PersistedState(server_id)
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
        self.server_methods = ServerMethods(self, self.persisted_state)

 
    def run(self):
        print('server %d started running' % self.server_id)

        # Main loop for consuming incoming requests
        while not self.stopped:
            request = {}
            timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)

            have_request = self.connection.poll(timeout)
            if not have_request:
                # If there is no message, assume the leader is dead
                # and run for leader
                print('server %d timed out waiting for a request' % self.server_id )
                if self.role == FOLLOWER:
                    self._run_for_leader()
                elif self.role = CANDIDATE:
                    self.role = FOLLOWER
                continue

            # Process a request
            request = self.connection.recv()
            print('server %d got request:' % self.server_id, request)

            # We have a request
            # Parse out the operation
            operation = request['operation']
            source_id = request['from']
    
            # prepare response
            response = {
                'type': 'response',
                'operation': operation,
                'from': self.server_id,
                'to': source_id
                }

            # Verify that the message is for us
            if self.server_id != request['to']:
                error = 'server {} received message for {}; ignoring. request {}'.format(
                    self.server_id, request['to'], request)
                print(error)
                response['status'] = False
                response['error'] = error
            else:
                method_return = self.server_methods.run_method(operation, request)
                response['status'] = method_return['status']
                response['method_return'] = method_return

            print('server %d about to return response ' 
                        % self.server_id, response)
            self.connection.send(response)

        print('server %d stopped running' % self.server_id)

    # Would it make more sense for this to be in ServerMethods? It's
    # not really callable from anywhere but this class, so for now
    # I'll leave it here
    def _run_for_leader(self):
        self.role = CANDIDATE
        new_term = self.persisted_state.get_current_term() + 1
        self.persisted_state.set_current_term = new_term
        self.persisted_state.set_voted_for = self.server_id
 
        request = {
            'from': self.server_id,
            'operation': 'request_vote'
            'term': new_term,
            'candiidate_id': self.server_id,
            'last_log_index': self.last_log_index,
            'last_log_term': self.last_log_term
        }

        statuses = [None] * self.server_count
        except_list = [self.server_id]
        statuses = broadcast_request(self.pipes, request, except_list)
        statuses[self.server_id] = True

 
    def stop(self):
        self.stopped = True
        return True

class ServerMethods():
    def __init__(self, my_server, persistent_state):
        self.my_server = my_server
        self.persistent_state = persistent_state
        self.registered_methods = {}
        self.registered_methods.update({'stop': self.stop})
 
    def run_method(self, operation, args):
        # methods are passed an argument dict containing whatever
        # data they require (passed from the source Raft node in the
        # incoming request)
        # methods must return a status of True or False, plus a dict
        # contained any data that it needs to return
        # The run_method method will then package this in a dict with 2
        # entries, 'status' for the True/False value, and 'output' for 
        # the data in the returned output dict.
        method = self.registered_methods[operation]
        result = {}
        if not method:
            result['status'] = False
            result['output'] = {'error': 'No method for operation %s' % operation}

        else:
            (result['status'], result['output']) = method(args)

        return result


    def stop(self, args):
        status = self.my_server.stop()
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
        return True

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
        statuses = broadcast_request(self.pipes, request, [])

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
    def __init__(self, target_id, connection, request):
        Thread.__init__(self)
        self.target_id = target_id
        self.connection = connection
        self.request = request
        self.result = None

    def run(self):
        self.request['to'] = self.target_id
        self.connection.send(self.request)

        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        self.result = {
            'status': None,
            'from': self.target_id
            }

        if self.connection.poll(timeout):
            response = self.connection.recv()
            self.result['status'] = response['status']
            self.result['response'] = response
        else:
            self.result['status'] = False

    def get_result(self):
        return self.result

def broadcast_request(pipes, request, except_list):
    server_count = len(pipes) - 1
    statuses = [False] * server_count

    threads = []
    for i in range(server_count):
        if i in except_list:
            continue
        thread = DoRequest(i, pipes[i].client_side, request)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
        result = thread.get_result()
        statuses[result['from']] = result['status']

    return statuses

''' This is the top level entry point for all subprocesses '''
def start_server(server_count, server_id, connection):
    print ('start_server', server_count, server_id)

    # Create and run the class which will consume entries on the queue
    # request_queues[server_id].
    node = RaftNode(server_count, server_id, connection)
    try:
        node.run()
    except KeyboardInterrupt:
        print('server got keyboard interrupt; exitting')



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

    server_count = int(sys.argv[1])
    if server_count < 1:
        print('Must have at least 1 server')
        exit()

    # Create the pipes
    pipes = [None] * (server_count + 1)
    for i in range(server_count + 1):
        pipes[i] = RaftPipe()

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
        connection = pipes[id].server_side
        processes[id] = mp.Process(
            target=start_server, 
            args=(server_count, id, connection)
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
