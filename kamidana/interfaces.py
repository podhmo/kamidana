import abc


class ILoader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def load(self, filename):
        pass

    @abc.abstractproperty
    def data(self):
        pass

    @abc.abstractmethod
    def additionals(self):
        pass


class IDriver(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def load(self, template_file):
        pass

    @abc.abstractmethod
    def dump(self, d, dst):
        pass

    @abc.abstractmethod
    def run(self, src, dst):
        pass
