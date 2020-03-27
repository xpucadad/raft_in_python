from log import Log

def main():
    log = Log(0)

    (status, entry) = log.get_entry(1)
    print("status: " + str(status))
    status = log.add_entry(1, 1, "Test Entry")
    print("satus: " + str(status))
    (status, entry) = log.get_entry(1)
    if status:
        print("entry: " + entry)
    else:
        print("entry for slot 1 not found")


if __name__ == "__main__":
    main()
