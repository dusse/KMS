from app import db

import enum

class ProgressStatus(enum.Enum):
    inprogress = ('inprogress', "in progress")
    done = ('done', "done")
    onreview = ('onreview', "on review")

    @property
    def tagname(self):
        return self.value[0]

    @property
    def description(self):
        return self.value[1]
