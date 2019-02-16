import abc

# TODO: using typing_extensions.Protocol?


class ITemplateLoader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def load(self, filename):  # Tuple[str, str, Callable[[], bool]]
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
