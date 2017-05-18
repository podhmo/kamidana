from kamidana.loader import Loader


class WithHeaderLoader(Loader):
    def load(self, filename):
        buf = []
        buf.append("# this file is auto generated by {!r}.\n\n".format(filename))
        buf.append(super().load(filename))
        return "".join(buf)
