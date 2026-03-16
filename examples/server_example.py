from babyros import node

if __name__ == "__main__":
    # Example usage
    server = node.Server("/example/topic", lambda: {"message": "Hello from server!"})
    server.start()

    time.sleep(100)

    server.delete()