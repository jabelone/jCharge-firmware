import json

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Settings:
    def __init__(self):
        self.socket = None

    def load(self):
        pass

    def save(self, message):
        pass

    def reset(self):
        pass
