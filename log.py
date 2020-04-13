from pymongo import MongoClient

class Log():
#    database_name="Raft"
#    collection_name="Log"
    def __init__(self, serverId):
        print("log: Hello, world!")
        self.serverId = serverId
        try:
            self.client = MongoClient('localhost:27017')
        except Exception as e:
            print('Connect to MongoDb failed: ', e)
        self.db = self.client.raft
#        self.collection = self.db.Log

    def add_entry(self, term, slot, entry):
        result = self.db.Log.replace_one(
            { "serverId": self.serverId, "slot": slot },
            {
                "serverId": self.serverId,
                "slot": slot,
                "term": term,
                "entry": entry
            },
            True
        )
        return result

    def get_entry(self, slot):
        le = self.db.Log.find_one({"slot": slot})
        if le == None:
            return (False, None, None)
        else:
            term = le["term"]
            entry = le["entry"]
            return (True, term, entry)
