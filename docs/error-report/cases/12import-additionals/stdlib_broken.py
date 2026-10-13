# fails inside stdlib (json.decoder); the stdlib frame is "internal",
# so where: points at this file and the raise site is filtered out.
import json

json.loads("{broken")
