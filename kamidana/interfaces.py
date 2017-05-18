import abc


class IProcessor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def process(self, create_function):
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
