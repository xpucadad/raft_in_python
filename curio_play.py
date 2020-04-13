import curio

async def countdown(n):
    while n > 0:
        print('T-minus', n)
        await curio.sleep(1)
        n -= 1

async def kid(x, y):
    try:
        print('Getting around to do my homework')
        await curio.sleep(1000)
        return x*y
    except curio.CancelledError:
        print("No go diggy die!")
        raise

async def parent():
    kid_task = await curio.spawn(kid, 37, 42)
    count_task = await curio.spawn(countdown, 10)

    await count_task.join()

    print("Are you done yet?")

    try:
        result = await curio.timeout_after(10, kid_task.join)
        print("Result:", result)
    except curio.TaskTimeout as e:
        print("We've got to go!")
        await kid_task.cancel()

if __name__ == '__main__':
    curio.run(parent, with_monitor=True)
