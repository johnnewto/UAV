import plugins


class PluginB(plugins.Base):

    def __init__(self):
        pass

    def start(self, buffer=None):
        print("Plugin B")
        if buffer is not None:
            print(f"Got buffer: {buffer.data.shape = } {buffer.pts = } {buffer.dts = }")