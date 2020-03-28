from log import Log

def main():
    log = Log(0)

    for i in range(10):
        (status, entry) = log.get_entry(i)
        print("status: " + str(status))
        data = "Test Entry " + str(i)
        status = log.add_entry(1, i, data)
        print("satus: " + str(status))
        (status, entry) = log.get_entry(i)
        if status:
            print("entry: " + entry)
        else:
            print(F'entry for slot {i} not found')


if __name__ == "__main__":
    main()
