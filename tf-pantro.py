#!/usr/bin/env python
import os, errno
import boto3
import argparse
from core import TerraformS3Lock
from core import TerraformRun
import argparse
import boto3
import contextlib
import copy
import getpass
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import yaml


def remove_old_file(filepath):
    try:
        os.remove(filepath)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def remote_state_config(region, bucket, key, path):
    remove_old_file('.terraform/terraform.tfstate')
    tf_args = ['remote',
               'config',
               '-backend=s3',
               '-backend-config=bucket={}'.format(bucket),
               '-backend-config=key={}'.format(key),
               '-backend-config=region={}'.format(region)]
    tfr = TerraformRun(tf_args)
    if path is not None:
        tfr.terraform_path = path
    tfr()


def get_terraform_modules(path):
    tf_args = ['get']
    tfr = TerraformRun(tf_args)
    if path is not None:
        tfr.terraform_path = path
    tfr()


def get_terraform_vars(region, bucket, prefix):
    remove_old_file('terraform.tfvars')
    client = boto3.client('s3', region)
    client.download_file(bucket, prefix + "terraform.tfvars", 'terraform.tfvars')


def run_terraform(args, tf_args):
    path = None
    if args.path:
        path = args.path
    tf_prefix = "terraform/" + args.env.lower() + "/" + args.prefix + "/"
    tf = TerraformS3Lock(args.region,
                         args.bucket,
                         tf_prefix + args.key)
    remote_state_config(args.region,
                        args.bucket,
                        tf_prefix + "terraform.tfstate",
                        path)
    get_terraform_vars(args.region,
                       args.bucket,
                       tf_prefix)
    get_terraform_modules(path)
    if args.force:
        tf.unlock()
    tf.lock()
    tfr = TerraformRun(tf_args)
    if path is not None:
        tfr.terraform_path = path
    tfr()
    tf.unlock()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r',
                        '--region',
                        default=os.environ.get('TF_VAR_region', None),
                        type=str)
    parser.add_argument('-e',
                        '--env',
                        default=os.environ.get('TF_VAR_env', None),
                        type=str)
    parser.add_argument('-b',
                        '--bucket',
                        default=os.environ.get('TF_VAR_state_bucket', None),
                        type=str)
    parser.add_argument('-p',
                        '--prefix',
                        default=os.environ.get('TF_VAR_state_prefix', None),
                        type=str)
    parser.add_argument('-k',
                        '--key',
                        default=os.environ.get('TF_VAR_tf_lock_key', None),
                        type=str)
    parser.add_argument('--path',
                        default=os.environ.get('TF_VAR_terraform_path', None),
                        type=str)
    parser.add_argument('--kms',
                        default=os.environ.get('TF_VAR_terraform_kms', None),
                        type=str)
    parser.add_argument('--force',
                        action='store_true')
    args, terraform = parser.parse_known_args()

    run_terraform(args, terraform)
