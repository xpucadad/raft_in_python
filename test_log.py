from log import Log

def main():
    log = Log(0)

    for i in range(10):
        (status, term, entry) = log.get_entry(i)
        print("status: " + str(status))
        data = "Test Entry " + str(i)
        status = log.add_entry(1, i, data)
        print("satus: " + str(status))
        (status, term, entry) = log.get_entry(i)
        if status:
            print('term: ' + str(term))
            print("entry: " + str(entry))
        else:
            print(F'entry for slot {i} not found')


if __name__ == "__main__":
    main()
