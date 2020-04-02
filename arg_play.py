import sys

def main(server_id):
    print('server_id: '+ server_id)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception('Need server id')
    else:
        main(sys.argv[1])
