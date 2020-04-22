import sys
import random
import queue
import time
import multiprocessing as mp
from threading import Thread

MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

class RaftServer:
    def __init__(self, server_count, server_id, pipes):
        print('server for %d created' % server_id)
        self.server_count = server_count
        self.server_id = server_id
        self.pipes = pipes
        self.requester_conn = pipes[server_id].requester_conn

        self.stopped = False
        self.server_methods = ServerMethods(self)

    def run(self):
        print('server for %d started' % self.server_id)
        response = {}
        while not self.stopped:
            timeout = random.randint(MIN_TIMEOUT, MAX_TIMEOUT)
            have_request = self.requester_conn.poll(timeout)
            if  not have_request:
                print('server %d timed out waiting for request' % self.server_id)
                
                continue
            else:
                request = self.requester_conn.recv()
                print('server %d got request:' % self.server_id, request)

            if self.server_id != request['to']:
                raise IndexError
                continue

            operation = request['operation']

            requester_id = request['from']
            out_conn = self.pipes[requester_id].out_conn

            response = {'from': self.server_id, 'to': requester_id,
                'operation': operation}
            result = {}

            # if operation == 'stop':
            #     print('Server got stop operation')
            #     self.stopped = True
            #     # result = {'status': True}
            #     result['status'] = True
            # else:
            print('server %d about to call method for' % server_id, operation)
            result = self.server_methods.call_method(operation, request)

            response['result'] = result
            response['status'] = result['status']

            self.requester_conn.send(response)

        print('server_id %d stopped' % self.server_id)

    def stop(self):
        self.stopped = True
        return True

class ServerMethods:
    def __init__(self, server):
        self.server = server
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
        return {'status': True, 'return': name}

    def goodbye(self, request):
        name = request['name']
        print('goodbye to %s from sender' % name, request['to'])
        return {'status': True, 'return': name}

    def stop(self, request):
        result = self.server.stop()
        return {'status': result}

def start_server(server_count, server_id, pipes):
    print('start server for id %d' % server_id)
    server = RaftServer(server_count, server_id, pipes)
    try:
        server.run()
    except KeyboardInterrupt:
        print('server got keyboard interrput; exitting')

class RaftPipe():
    def __init__(self, requester_conn, responder_conn):
        self.requester_conn = requester_conn
        self.responder_conn = responder_conn

    def close(self):
        self.requester_conn.close()
        self.responder_conn.close()

class DoRequest(Thread):
    def __init__(self, target_id, pipe, request):
        print('DoRequest pipe', pipe)
        Thread.__init__(self)
        self.target_id = target_id
        self.request = request
        self.pipe = pipe
        self.result = None

    def run(self):
        print('this is running in a thread')
        request['to'] = self.target_id
        self.pipe.requester_conn.send(request)

        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        self.result = {'status': None, 'from_id': self.target_id}
        responder_conn = self.pipe.responder_conn
        have_response = responder_conn.poll(timeout)
        if not have_response:
            # we timed out; assume we'll never got a response
            # (at some point we'll need to deal with responeso
            # that come in after timeout - that is ignore them)
            self.result['status'] = False 
        else:
            response = response_conn.recv()
            print('respose in thread', response)
            self.result['status'] = response['status']

    def get_result(self):
        return self.result

def broadcast_request(pipes, request, except_list):
    print('broadcast_request pipes', pipes)
    server_count = len(pipes) - 1
    responses = [False] * server_count
    pending_responses = 0 

    threads = []
    for i in range(server_count):
        if i in except_list:
            continue
        # connection = pipes[i].requester_conn
        print('creating thread for %d to handle'%i,request)
        thread = DoRequest(i, pipes[i], request)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
        result = thread.get_result()
        responses[result['from_id']] = result['status']
        print('Current responses', responses)

    return responses


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('must provide server count')
        exit()

    server_count = int(sys.argv[1])
    if server_count < 1:
        print('must specify 1 or more servers')
        exit()

    pipes = [None] * (server_count+1)

    for i in range(server_count+1):
        (requester_conn, responder_conn) = mp.Pipe()
        pipe = RaftPipe(requester_conn, responder_conn)
        pipes[i] = pipe

    processes = [None] * server_count
    for id in range(server_count):
        processes[id] = mp.Process(target=start_server, args=(server_count, id, pipes))

    for p in processes:
        p.start()

    time.sleep(1)
    my_id = server_count


    # Issue a request to each server
    request = {
        'type': 'request',
        'from': my_id,
        'operation': 'hello',
        'name': 'Ken'
    }
 
    except_list = []
    responses = broadcast_request(pipes, request, except_list)
    print('responses form hello', responses)

    # request['operation'] = 'goodbye'
    # request['name'] = 'hal'

    # responses = broadcast_request(pipes, request, except_list)
    # print('responses from goodbye', responses)


    request['operation'] = 'stop'

    responses = broadcast_request(pipes, request, except_list)
    print('responses from stop', responses)
 
    for i in range(server_count):
        pipes[i].close()

    for p in processes:
        p.join()
