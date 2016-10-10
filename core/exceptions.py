class TerraformLockBaseException(Exception):
    """
    Base class for TerraformLock errors.

    :ivar msg: Descriptive message associated with the exception
    """

    def __init__(self, **kwargs):
        msg = self.fmt.format(**kwargs)
        Exception.__init__(self, msg)
        self.kwargs = kwargs


class TerraformLockedException(TerraformLockBaseException):
    """
    An exception occured when trying to lock Terraform infrastructure

    :ivar user: The user that owns the lock
    :ivar time: Creation time of the lock
    :ivar hash: Hash of the lock
    """

    fmt = 'Terraform infarstructure was locked by {user} at {time}'


class TerraformUnlockException(TerraformLockBaseException):
    fmt = 'Unable to unlock Terraform state'