import enum


class Role(enum.Enum):
    OWNER = 'owner'
    SUPERVISOR = 'supervisor'
    WORKER = 'worker'