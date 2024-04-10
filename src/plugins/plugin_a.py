import plugins


class PluginA(plugins.Base):

    def __init__(self):
        pass

    def start(self, buffer = None):
        print("Plugin A")