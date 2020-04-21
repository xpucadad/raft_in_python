import sys
import random
import queue
import time
import multiprocessing as mp

MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

class RaftServer:
    def __init__(self, server_count, server_id, pipes):
        self.server_count = server_count
        self.server_id = server_id
        self.pipes = pipes
        self.in_conn = pipes[server_id].in_conn

        self.stopped = False
        self.server_methods = ServerMethods(self)

    def run(self):
        response = {}
        while not self.stopped:
            timeout = random.randint(MIN_TIMEOUT, MAX_TIMEOUT)
            have_request = self.in_conn.poll(timeout)
            if  not have_request:
                print('server %d timed out waiting for request' % self.server_id)
                continue
            else:
                request = self.in_conn.recv()
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
            result = self.server_methods.call_method(operation, request)

            response['result'] = result
            response['status'] = result['status']

            out_conn.send(response)

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
        server = RaftServer(server_count, server_id, pipes)
        try:
            server.run()
        except KeyboardInterrupt:
            print('server got keyboard interrput; exitting')

class RaftPipe():
    def __init__(self, in_conn, out_conn):
        self.in_conn = in_conn
        self.out_conn = out_conn

    def close(self):
        self.in_conn.close()
        self.out_conn.close()

def broadcast_request(pipes, request):
    server_count = len(pipes) - 1
    for i in range(server_count):
        request['to'] = i
        out_conn = pipes[i].out_conn
        out_conn.send(request)

    pending_responses = server_count
    my_id = server_count
    in_conn = pipes[my_id].in_conn
    while pending_responses:
        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        have_response = in_conn.poll(timeout)
        if not have_response:
            print('server %d timed out waiting for response' % my_id)
            continue
        else:
            response = in_conn.recv()
            print('server %d got respones' % my_id, response)
            pending_responses -= 1



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
        (in_conn, out_conn) = mp.Pipe()
        pipe = RaftPipe(in_conn, out_conn)
        pipes[i] = pipe

    processes = [None] * server_count
    for id in range(server_count):
        processes[id] = mp.Process(target=start_server, args=(server_count, id, pipes))

    for p in processes:
        p.start()

    my_id = server_count


    # Issue a request to each server
    request = {
        'type': 'request',
        'from': my_id,
        'operation': 'hello',
        'name': 'Ken'
    }

    broadcast_request(pipes, request)

    request['operation'] = 'goodbye'
    request['name'] = 'hal'

    broadcast_request(pipes, request)

    request['operation'] = 'stop'

    broadcast_request(pipes, request)
 
    for i in range(server_count):
        pipes[i].close()

    for p in processes:
        p.join()
