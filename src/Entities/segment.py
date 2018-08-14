from uuid import uuid4


class Segment:
    """
    type: 'func',
    """
    def __init__(self, _type = 'func'):
        self.type = _type
        self.id = uuid4()