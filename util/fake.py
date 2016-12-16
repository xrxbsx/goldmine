"""A few fake container classes to make some functions work."""

class FakeContextMember():
    def __init__(self, member, bot):
        self.message = member
        self.bot = bot

class FakeMessageMember():
    def __init__(self, member):
        self.author = member
        self.server = member.server
        self.channel = list(member.server.channels)[0]

class FakeEmbed():
    def __init__(self, **kwargs):
        print('color' + str(kwargs))
    def set_author(self, **kwargs):
        print(kwargs)
    def set_thumbnail(self, **kwargs):
        print(kwargs)
    def set_footer(self, **kwargs):
        print(kwargs)
    def add_field(self, **kwargs):
        print(kwargs)

class FakeObject():
    def __init__(self, value=None):
        self.value = value
    def __getattr__(self, name):
        return self.value
