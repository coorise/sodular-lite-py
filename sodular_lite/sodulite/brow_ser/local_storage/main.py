import json


class LocalStorage:
    storage = {}

    @classmethod
    def getItem(cls, key):
        return cls.storage.get(key, None)

    @classmethod
    def setItem(cls, key, value):
        cls.storage[key] = value

    @classmethod
    def removeItem(cls, key):
        if key in cls.storage:
            del cls.storage[key]

    @classmethod
    def clear(cls):
        cls.storage = {}
