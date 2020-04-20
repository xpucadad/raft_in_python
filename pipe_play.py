import sys
import random
import queue
import time
import multiprocessing as mp

SERVER_COUNT = 5
MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

class RaftServer:
    def __init__(self, server_id, pipes):
        self.server_id = server_id
        self.pipes = pipes
        self.in_conn = pipes[server_id].in_conn

        self.stopped = False

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

            response = {'from': self.server_id, 'to': requester_id}

            if operation == 'stop':
                self.stopped = True
            elif operation == 'hello':
                print('hello')
                response['return'] = 'hello'

            response['operation'] = request['operation']
            response['status'] = True

            out_conn.send(response)

        print('server_id %d stopped' % self.server_id)


def start_server(server_id, pipes):
        server = RaftServer(server_id, pipes)
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

if __name__ == '__main__':

    pipes = [None] * (SERVER_COUNT+1)

    for i in range(SERVER_COUNT+1):
        (in_conn, out_conn) = mp.Pipe()
        pipe = RaftPipe(in_conn, out_conn)
        pipes[i] = pipe

    processes = [None] * SERVER_COUNT
    for id in range(SERVER_COUNT):
        processes[id] = mp.Process(target=start_server, args=(id, pipes))

    for p in processes:
        p.start()

    my_id = SERVER_COUNT


    # Issue a request to each server
    request = {
        'type': 'request',
        'from': my_id,
        'operation': 'hello'
    }

    for i in range(SERVER_COUNT):
        request['to'] = i
        out_conn = pipes[i].out_conn
        print('client sending request to %d' % i, request)
        out_conn.send(request)

    # wait for responses
    pending_responses = SERVER_COUNT
    in_conn = pipes[my_id].in_conn
    while pending_responses:
        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        have_response = in_conn.poll(timeout)
        if not have_response:
            print('timed out waiting for response')
            continue
        else:
            response = in_conn.recv()
            print('got response', response)
            pending_responses -= 1

    request['operation'] = 'stop'

    for i in range(SERVER_COUNT):
        request['to'] = i
        out_conn = pipes[i].out_conn
        out_conn.send(request)

    # wait for responses
    pending_responses = SERVER_COUNT
    in_conn = pipes[my_id].in_conn
    while pending_responses:
        timeout = random.uniform(MIN_TIMEOUT, MAX_TIMEOUT)
        have_response = in_conn.poll(timeout)
        if not have_response:
            print('timed out waiting for response')
            continue
        else:
            response = in_conn.recv()
            print('got response', response)
            pending_responses -= 1

    for i in range(SERVER_COUNT):
        pipes[i].close()

    for p in processes:
        p.join()
