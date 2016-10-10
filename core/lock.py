import os
import pwd
import io
import hashlib
import json
import abc
from datetime import datetime
import boto3
import botocore
from .exceptions import (
    TerraformLockedException, TerraformUnlockException
)


class TerraformLock(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._is_locked = False
        self._contents = {}
        self._hash = None

    @property
    def user(self):
        return self._contents['User']

    @property
    def time(self):
        return self._contents['Time']

    @property
    def hash(self):
        return self._hash

    @property
    def locked(self):
        return self._is_locked

    def _set_contents(self):
        self._contents['Time'] = datetime.utcnow().isoformat("T")
        self._contents['User'] = pwd.getpwuid(os.getuid())[0]

    def _set_hash(self):
        self._hash = hashlib.md5(json.dumps(self._contents).encode('utf-8')).hexdigest()

    @abc.abstractmethod
    def lock(self):
        """Lock Terraform Infrastructure"""

    @abc.abstractmethod
    def unlock(self):
        """Unlock Terraform Infrastructure"""


class TerraformS3Lock(TerraformLock):

    def __init__(self, region, bucket, key):
        TerraformLock.__init__(self)
        self._bucket = bucket
        self._key = key
        self._client = boto3.client('s3', region,)

    def _read_remote_lock(self):
        try:
            remote_lock = self._client.get_object(Bucket=self._bucket,
                                                  Key=self._key)
            return json.loads(remote_lock['Body'].read().decode('utf-8'))
        except botocore.exceptions.ClientError:
            return None

    def _get_remote_lock(self):
        remote_contents = self._read_remote_lock()
        if remote_contents is None:
            self._is_locked = False
            return None
        else:
            self._is_locked = True
            return remote_contents

    def lock(self):
        self._set_contents()
        self._set_hash()

        lock_contents = self._get_remote_lock()
        if self._is_locked:
            raise TerraformLockedException(user=lock_contents['User'], time=lock_contents['Time'])
        else:
            try:
                self._client.put_object(Bucket=self._bucket,
                                        Key=self._key,
                                        Body=io.BytesIO(json.dumps(self._contents).encode('utf-8')),
                                        ContentType='application/json')
                self._is_locked = True
            except Exception as e:
                raise e

    def unlock(self):
        try:
            response = self._client.delete_object(Bucket=self._bucket, Key=self._key)
            if response['DeleteMarker'] is True:
                self._is_locked = False
            else:
                raise TerraformUnlockException
        except botocore.exceptions.ClientError:
            raise TerraformUnlockException
        except Exception as e:
            raise e
