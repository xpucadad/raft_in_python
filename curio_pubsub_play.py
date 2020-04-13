from curio import run, TaskGroup, Queue, sleep

messages = Queue()
subscribers = set()

# Dispatch task that forwards incoming messages to subscribers
async def dispatcher():
    while True:
        msg = await messages.get()
        for q in list(subscribers):
            await q.put(msg)

# Publish a messages
async def publish(msg):
    await messages.put(msg)

# A sample subscriber task
async def subscriber(name):
    queue = Queue()
    subscribers.add(queue)
    try:
        while True:
            msg = await queue.get()
            print(name, 'got', msg)
    finally:
        subscribers.discard(queue)

# A sample producer task
async def producer():
    for i in range(10):
        await publish(i)
        await sleep(0.1)

async def main():
    async with TaskGroup() as g:
        await g.spawn(dispatcher)
        await g.spawn(subscriber, 'child1')
        await g.spawn(subscriber, 'child2')
        await g.spawn(subscriber, 'child3')
        ptask = await g.spawn(producer)
        await ptask.join()
        await g.cancel_remaining()

if __name__ == '__main__':
    run(main)
