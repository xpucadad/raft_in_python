# raft_in_python
For learning about raft by implementing it in Python

# Design

Use Python RPC server and client to send messages between the raft servers.

Create a single Python program which implements all three Raft states. This will be run multiple times.

Not yet sure how to handle changes to the configuration - haven't seen how this is done according to the Raft documents.

# Issues
What in the correct way to stop the server. I seem to remember that something other than serve_forever can be called and this will provide a clean way to exit. (Forced exit can be caused using ^C.)
