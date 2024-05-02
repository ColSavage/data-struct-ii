class HashTable:
    def __init__(self, size):
        self.size = size
        self.keys = [None] * size
        self.values = [None] * size

    def hash_function(self, key):
        return hash(key) % self.size

    def insert(self, key, value):
        index = self.hash_function(key)

        # Linear probing to handle collisions
        while self.keys[index] is not None:
            if self.keys[index] == key:
                # Key already exists, update its value
                self.values[index] = value
                return
            index = (index + 1) % self.size

        # Insert the key and value
        self.keys[index] = key
        self.values[index] = value

    def search(self, key):
        index = self.hash_function(key)

        # Linear probing to find the key
        while self.keys[index] is not None:
            if self.keys[index] == key:
                return self.values[index]
            index = (index + 1) % self.size

        # Key not found
        return None

