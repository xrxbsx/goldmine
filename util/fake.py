"""A few fake container classes to make some functions work."""

class FakeContextMember():
    def __init__(self, member):
        self.message = member

class FakeMessageMember():
    def __init__(self, member):
        self.author = member
        self.server = member.server
        self.channel = list(member.server.channels)[0]
