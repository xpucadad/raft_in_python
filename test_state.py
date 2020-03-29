from server_state import *
from server_state import ServerState

def main():
    state = ServerState()
    print (state.get_state_string())
    print (state.set_state(LEADER))
    print (state.set_state(CANDIDATE))

    cState = state.get_state_string()

    try:
        state.set_state(4)
    except ValueError:
        print('Invalid state specified. State remains at ' + cState + '\n')

    print(state.get_state_string())

if __name__ == '__main__':
    main()
