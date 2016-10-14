from core.utils import *
from core.lock import *
import tempfile

#os.path.isfile('')
class Pantropy(object):
    def __init__(self, enviroment):
        self.env_path = tempfile.mkdtemp(prefix="tf_env_")
        print self.env_path
        shutil

Pantropy('staging')