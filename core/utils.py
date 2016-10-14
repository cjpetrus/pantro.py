import argparse
import errno
import os
import shutil
import boto3
import botocore
from core import TerraformRun
from core import TerraformS3Lock


# def create_env(dirpath):
#     env_path = tempfile.mkdtemp()
#     #shutil.rmtree(dirpath)
#     return env_path


def remove_old_file(filepath):
    try:
        os.remove(filepath)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def copy_directory(src, dest):
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


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


def get_account_id():
    iam = boto3.client('iam')
    users = iam.list_users()['Users']
    roles = iam.list_roles()['Roles']

    if users:
        arn = users[0]['Arn']
    else:
        for role in roles:
            try:
                arn = iam.get_role(RoleName=role['RoleName'])['Role']['Arn']
                break
            except Exception as e:
                pass


def get_account_id():
    iam = boto3.client('iam')
    users = iam.list_users()['Users']
    roles = iam.list_roles()['Roles']

    if users:
        arn = users[0]['Arn']
    else:
        for role in roles:
            try:
                arn = iam.get_role(RoleName=role['RoleName'])['Role']['Arn']
                break
            except Exception as e:
                pass


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


def s3_file_exist(filename):
    s3 = boto3.resource('s3')
    exists = False

    try:
        s3.Object('my-bucket', filename).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            exists = False
        else:
            raise e
    else:
        exists = True

    print(exists)


def parse_arguments():
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

    # run_terraform(args, terraform)
    return (args, terraform)
