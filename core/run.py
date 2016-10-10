import subprocess
from distutils.spawn import find_executable


class TerraformRun(object):

    def __init__(self, terraform_arguments):
        self._terraform_path = find_executable('terraform')
        self._terraform_arguments = terraform_arguments

    def __call__(self):
        self._terraform_arguments.insert(0, self.terraform_path)
        p = subprocess.Popen(self._terraform_arguments)
        stdout, stderr = p.communicate()

    @property
    def terraform_path(self):
        return self._terraform_path

    @terraform_path.setter
    def terraform_path(self, path):
        self._terraform_path = path
