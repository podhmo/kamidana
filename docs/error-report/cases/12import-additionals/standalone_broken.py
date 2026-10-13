# the file exists but fails while being imported; the real
# ModuleNotFoundError should surface instead of the builtin fallback.
import no_such_module_xyz
