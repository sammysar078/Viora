class Registry:
    def __init__(self): self.items=[]
    def add(self,name,register): self.items.append((name,register))
    async def load(self,app,ctx):
        for _,fn in self.items:
            r=fn(app,ctx)
            if hasattr(r,'__await__'): await r
