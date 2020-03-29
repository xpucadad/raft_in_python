FOLLOWER = 0
CANDIDATE = 1
LEADER = 2

names = [None] * 3
names[FOLLOWER] = 'Follower'
names[CANDIDATE] = 'Candidate'
names[LEADER] = 'Leader'

class ServerState():

    def __init__(self):
        self.state = FOLLOWER

    def set_state(self, newState):
        if newState < 0 or newState > 2:
            raise ValueError("Invalid state value: " + str(newState))
        else:
            self.state = newState
        return self.state

    def get_state(self):
        return (self.state)

    def get_state_string(self):
        return names[self.state]
