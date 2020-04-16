import random
from server_state import *
from server_state import PersistedState

TEST_SERVER_ID = 9

def main(reset):
    print('reset %d' % reset)
    state = PersistedState(TEST_SERVER_ID)

    if reset:
        print(state._reset())

    voted_for = state.get_voted_for()
    current_term = state.get_current_term()

    print('initial voted for', voted_for)
    print('initial current term', current_term)

    voted_for = random.randint(0,9)
    current_term += 1

    print('state after voted for update',
            state.set_voted_for(voted_for))
    print('state after current term uptade',
            state.set_current_term(current_term))

if __name__ == '__main__':
    import sys
    reset = False
    print('len of argv %d' % len(sys.argv))
    if len(sys.argv) > 1:
        print(sys.argv)
        if sys.argv[1] == 'r':
            reset = True
    main(reset)
