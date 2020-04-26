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
                'from': self.node_id, 'to': requester_id,
                'operation': operation
                }
            result = {}

            # if operation == 'stop':
            #     print('Server got stop operation')
            #     self.stopped = True
            #     # result = {'status': True}
            #     result['status'] = True
            # else:
            print('node %d about to call method for' % self.node_id, 
                operation)
            result = self.node_methods.call_method(operation, request)

            response['result'] = result
            response['status'] = result['status']

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

    # def register_method(self, operation, method):
    #     self.registered_methods['operation'] = method

    def call_method(self, operation, dict):
        method = self.registered_methods[operation]
        if method:
            result = method(dict)
        else:
            error = 'No such method' + operation
            result =  {'status': False, 'error': error}

        return result

    def hello(self, request):
        name = request['name']
        sender = request['to']
        print('hello %s from server %d' % (name, sender))
        return {'status': True, 'return_args': {'name': name}}

    def goodbye(self, request):
        name = request['name']
        print('goodbye to %s from sender' % name, request['to'])
        return {'status': True, 'return_args': {'name': name}}

    def stop(self, request):
        result = self.node.stop()
        return {'status': result, 'return_args': None}

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

    def broadcast_request(self, request, exclude=[]):
        statuses = [None] * self.node_count
        return_args = [None] * self.node_count

        threads = []
        for target_id in range(node_count):
            if target_id in exclude:
                continue

            thread = DoRequest(
                target_id, 
                pipes[target_id].client_side, 
                request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
            result = thread.get_results()
            from_id = result['from']

            statuses[from_id] = result['status']
            return_args[from_id] = result['return_angs']

        return (statuses, return_args)

class DoRequest(Thread):
    def __init__(self, target_id, connection, request):
        Thread.__init__(self)
        self.target_id = target_id
        self.request = request
        self.connection = connection
        self.result = {}

    def run(self):
        request['to'] = self.target_id
        print('thread', 'about to send to %d:' % self.target_id, request)
        self.connection.send(request)

        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        self.results = {'status': None, 'from': self.target_id}
        
        if self.connection.poll(timeout):
            response = self.connection.recv()
            print('response from %d in thread' % self.target_id, response)
            self.results['status'] = response['status']
            self.results['return_args'] = response['return_args']
        else:
            print('timed out waiting for response from %d' % self.target_id)
            self.results['status'] = False
            self.results['return_args'] = None

    def get_results(self):
        return self.results

# def broadcast_request(pipes, request, except_list):
#     server_count = len(pipes) - 1
#     responses = [False] * server_count

#     threads = []
#     for i in range(server_count):
#         if i in except_list:
#             continue
#         # connection = pipes[i].requester_conn
#         print('creating thread for %d to handle'%i,request)
#         thread = DoRequest(i, pipes[i].client_side, request)
#         threads.append(thread)
#         thread.start()

#     for thread in threads:
#         thread.join()
#         result = thread.get_result()
#         print('thread: got result from %d:' % i, result)
#         responses[result['from_id']] = result['status']
#         print('Current responses', responses)

#     return responses

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

    # request['operation'] = 'goodbye'
    # request['name'] = 'hal'

    # responses = broadcast_request(pipes, request, except_list)
    # print('responses from goodbye', responses)

    request['operation'] = 'stop'

    results = ncc.broadcast_request(request, [])
    print('results from stop', results)
 
    for i in range(node_count):
        pipes[i].close()

    for p in processes:
        p.join()
