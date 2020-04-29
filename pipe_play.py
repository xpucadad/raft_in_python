import sys
import random
import queue
import time
import multiprocessing as mp
from threading import Thread

MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

class RaftNode:
    def __init__(self, node_count, node_id, connection):
        print('node for %d created' % node_id)
        self.node_count = node_count
        self.node_id = node_id
        self.connection = connection

        self.stopped = False
        self.node_methods = RaftNodeMethods(self)

    def run(self):
        print('node for %d started' % self.node_id)
        response = {}
        while not self.stopped:
            timeout = random.randint(MIN_TIMEOUT, MAX_TIMEOUT)
            have_request = self.connection.poll(timeout)
            if  not have_request:
                print('server %d timed out waiting for request' % self.node_id)
                continue
            else:
                request = self.connection.recv()
                print('server %d got request:' % self.node_id, request)

            if self.node_id != request['to']:
                raise IndexError
                continue

            operation = request['operation']

            requester_id = request['from']

            response = {
                'type': 'response',
                'operation': operation,
                'from': self.node_id, 
                'to': requester_id
                }

            print('node %d about to call method for' % self.node_id, operation)
            (response['status'], response['return_args']) = self.node_methods.call_method(operation, request)
            print('return values from method', response['status'], response['return_args'])

            self.connection.send(response)

        print('server %d stopped' % self.node_id)

    def stop(self):
        self.stopped = True
        return True

class RaftNodeMethods:
    def __init__(self, node):
        self.node = node
        self.registered_methods = {}
        self.registered_methods['hello'] = self.hello
        self.registered_methods['goodbye'] = self.goodbye
        self.registered_methods['stop'] = self.stop
        # self.register_method('hello', self.hello)
        # self.register_method('goodbye', self.goodbye)

    #     self.registered_methods['operation'] = method

    # Methods should always return a twople. The 1st entry is
    # either True or False and the second is a dictionary of return
    # arguments or values. This twople will then be returne to 
    # the caller of call_method
    def call_method(self, operation, request):
        method = self.registered_methods[operation]
        if method:
            result = method(request)
        else:
            error = 'No such method' + operation
            result =  (False, {'error': error})

        return result

    def hello(self, request):
        name = request['name']
        sender = request['to']
        print('hello %s from server %d' % (name, sender))
        return (True, {'name': name})

    def goodbye(self, request):
        name = request['name']
        print('goodbye to %s from sender' % name, request['to'])
        return (True, {'name': name})

    def stop(self, request):
        result = self.node.stop()
        return (result, {})

def start_node(node_count, node_id, connection):
    print('start node for id %d' % node_id)
    node = RaftNode(node_count, node_id, connection)
    try:
        node.run()
    except KeyboardInterrupt:
        print('node got keyboard interrput; exitting')

class NodeCommunicationController():
    def __init__(self, node_count, node_id, pipes):
        self.node_count = node_count
        self.node_id = node_id
        self.pipes = pipes

    # The request is a dictionary. It should have at
    # least the 'operation' and 'from' entries defined. The code in DoRequest
    # will add the other required header fields ('type' and 'to')
    # It must also contain entries for any additional arguments are needed
    # by the method call. The exclude list should include the id's of 
    # any nodes that the request should not be sent to (e.g. the sender
    # of a request vote request).
    def broadcast_request(self, request, exclude=[]):
        statuses = [None] * self.node_count
        return_args = [None] * self.node_count
        full_responses = [None] * self.node_count

        request['type'] = 'request'

        threads = [None] * self.node_count
        for target_id in range(node_count):
            if target_id in exclude:
                continue

            thread = DoRequest(
                target_id, 
                self.pipes[target_id].client_side, 
                request)
            threads[target_id] = thread
            thread.start()

        for id in range(len(threads)):
            full_response = {
                'type': 'response',
                'operation': request['operation'],
                'to': request['from'],
                'from': id
            }
            thread = threads[id]
            if not thread:
                continue
            thread.join()
            result = thread.get_results()

            status = result[0]
            ra = result[1]
            statuses[id] = status
            return_args[id] = ra
            full_response.update({
                'status': status,
                'return_args': ra,
                })
            full_responses[id] = full_response

        return (statuses, return_args, full_responses)

class DoRequest(Thread):
    def __init__(self, target_id, connection, request):
        Thread.__init__(self)
        self.target_id = target_id
        self.request = request
        self.connection = connection
        self.request['to'] = target_id
        self.status = False

    def run(self):
        print('thread', 'about to send to %d:' % self.target_id, request)
        self.connection.send(request)

        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        # self.results = {'status': None, 'from': self.target_id}
        
        if self.connection.poll(timeout):
            reply = self.connection.recv()
            print('response from %d in thread' % self.target_id, reply)
            self.status = reply['status']
            self.return_args = reply['return_args']

        else:
            print('timed out waiting for response from %d' % self.target_id)
            self.status = False
            self.return_args = {}
            # self.results['status'] = False
            # self.results['return_args'] = None

    def get_results(self):
        return (self.status, self.return_args)

class RaftPipe():
    def __init__(self):
        (self.client_side, self.server_side) = mp.Pipe()

    def close(self):
        self.client_side.close()
        self.server_side.close()


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('must provide server count')
        exit()

    node_count = int(sys.argv[1])
    if node_count < 1:
        print('must specify 1 or more nodes')
        exit()

    # A slot for each server, plus one for control
    pipes = [None] * (node_count+1)

    for id in range(node_count+1):
        pipes[id] = RaftPipe()

    # A server process for each server to handlie incomming messages
    processes = [None] * node_count
    for id in range(node_count):
        connection = pipes[id].server_side
        processes[id] = mp.Process(target=start_node, 
                            args=(node_count, id, connection))

    for p in processes:
        p.start()

    # The control id is for the code below. It should be one larger than
    # the largest node_id. This should prevent any other nodes from 
    # from treating it like a sibling.
    control_id = node_count
    ncc = NodeCommunicationController(node_count, control_id, pipes)

    '''
    Simple testing code
    '''

    # Issue a request to each server
    request = {
        'type': 'request',
        'from': control_id,
        'operation': 'hello',
        'name': 'Ken'
    }
 
    exclude = []
    # if we have more than 1 server, skip the first.
    if node_count > 1:
        exclude.append(0)

    results = ncc.broadcast_request(request, exclude)
    print('results from hello', results)

    request['operation'] = 'stop'

    results = ncc.broadcast_request(request, [])
    print('results from stop', results)
 
    for i in range(node_count):
        pipes[i].close()

    for p in processes:
        p.join()
