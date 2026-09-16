# a --loader target that fails while being imported.
import no_such_module_xyz
from kamidana.loader import TemplateLoader

MyLoader = TemplateLoader
