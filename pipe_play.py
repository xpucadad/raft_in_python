import sys
import random
import queue
import time
import multiprocessing as mp
from threading import Thread

MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

class RaftServer:
    def __init__(self, server_count, server_id, connection):
        print('server for %d created' % server_id)
        self.server_count = server_count
        self.server_id = server_id
        self.connection = connection

        self.stopped = False
        self.server_methods = ServerMethods(self)

    def run(self):
        print('server for %d started' % self.server_id)
        response = {}
        while not self.stopped:
            timeout = random.randint(MIN_TIMEOUT, MAX_TIMEOUT)
            have_request = self.connection.poll(timeout)
            if  not have_request:
                print('server %d timed out waiting for request' % self.server_id)
                
                continue
            else:
                request = self.connection.recv()
                print('server %d got request:' % self.server_id, request)

            if self.server_id != request['to']:
                raise IndexError
                continue

            operation = request['operation']

            requester_id = request['from']

            response = {
                'type': 'response',
                'from': self.server_id, 'to': requester_id,
                'operation': operation
                }
            result = {}

            # if operation == 'stop':
            #     print('Server got stop operation')
            #     self.stopped = True
            #     # result = {'status': True}
            #     result['status'] = True
            # else:
            print('server %d about to call method for' % self.server_id, 
                operation)
            result = self.server_methods.call_method(operation, request)

            response['result'] = result
            response['status'] = result['status']

            self.connection.send(response)

        print('server %d stopped' % self.server_id)

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

def start_server(server_count, server_id, connection):
    print('start server for id %d' % server_id)
    server = RaftServer(server_count, server_id, connection)
    try:
        server.run()
    except KeyboardInterrupt:
        print('server got keyboard interrput; exitting')


class DoRequest(Thread):
    def __init__(self, target_id, connection, request):
        Thread.__init__(self)
        self.target_id = target_id
        self.request = request
        self.connection = connection
        self.result = None

    def run(self):
        request['to'] = self.target_id
        print('thread', 'about to send to %d:' % self.target_id, request)
        self.connection.send(request)

        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        self.result = {'status': None, 'from_id': self.target_id}
        
        if self.connection.poll(timeout):
            response = self.connection.recv()
            print('response from %d in thread' % self.target_id, response)
            self.result['status'] = response['status']
        else:
            print('timed out waiting for resposne from %d' % self.target_id)
            self.result['status'] = False

    def get_result(self):
        return self.result

def broadcast_request(pipes, request, except_list):
    server_count = len(pipes) - 1
    responses = [False] * server_count

    threads = []
    for i in range(server_count):
        if i in except_list:
            continue
        # connection = pipes[i].requester_conn
        print('creating thread for %d to handle'%i,request)
        thread = DoRequest(i, pipes[i].client_side, request)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
        result = thread.get_result()
        print('thread: got result from %d:' % i, result)
        responses[result['from_id']] = result['status']
        print('Current responses', responses)

    return responses

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

    server_count = int(sys.argv[1])
    if server_count < 1:
        print('must specify 1 or more servers')
        exit()

    # A slot for each server, plus one for control
    pipes = [None] * (server_count+1)

    for i in range(server_count+1):
        pipes[i] = RaftPipe()

    # A server process for each server to handlie incomming messages
    processes = [None] * server_count
    for id in range(server_count):
        connection = pipes[id].server_side
        processes[id] = mp.Process(target=start_server, 
                            args=(server_count, id, connection))

    for p in processes:
        p.start()

    # all_alive = False
    # alive = [False] * server_count
    # loop = 0
    # while not all_alive:
    #     all_alive = True
    #     for i in range(server_count):
    #         if not alive[i]:
    #             alive[i] = processes[i].is_alive()
    #             if alive[i]:
    #                 print('server %d is alive' % i)
    #             else:
    #                 print('server %d is NOT alive' % i)
    #                 all_alive = False
    #     loop += 1
    # print('alive check ran %d times' % loop, alive)

    control_id = server_count


    # Issue a request to each server
    request = {
        'type': 'request',
        'from': control_id,
        'operation': 'hello',
        'name': 'Ken'
    }
 
    except_list = []
    # if we have more than 1 server, skip the first.
    if server_count > 1:
        except_list.append(0)
    responses = broadcast_request(pipes, request, except_list)
    print('responses from hello', responses)

    # request['operation'] = 'goodbye'
    # request['name'] = 'hal'

    # responses = broadcast_request(pipes, request, except_list)
    # print('responses from goodbye', responses)

    request['operation'] = 'stop'

    responses = broadcast_request(pipes, request, [])
    print('responses from stop', responses)
 
    for i in range(server_count):
        pipes[i].close()

    for p in processes:
        p.join()
