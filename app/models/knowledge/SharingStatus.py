from app import db

import enum

class SharingStatus(enum.Enum):
    private = ('private', "private")
    shared = ('shared', "shared")

    @property
    def tagname(self):
        return self.value[0]

    @property
    def description(self):
        return self.value[1]
