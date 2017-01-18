import importlib

class DynaImport(object):
    def __init__(self, module):
        self.import_name = module
        self.imported = False
        self.module = None

    def ensure_imported(self):
        if not self.imported:
            self.module = importlib.import_module(self.import_name)
            self.imported = True

    def __getattr__(self, attr):
        self.ensure_imported()
        return getattr(self.module, attr)

def load(name):
    return DynaImport(name)

# minified version
'''import importlib as i
class D:
 def __init__(s,n):s.i=n;s.s=0;s.m=0
 def e(s):
  if not s.s:s.m=i.import_module(s.i);s.s=1
 def __getattr__(s,a):s.e();return getattr(s.m,a)
load=lambda n:D(n)'''
