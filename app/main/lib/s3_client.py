import boto3
from botocore.client import Config

from flask import current_app as app

from app.main.lib.error_log import ErrorLog

MINIO_HOST = "minio:9000"
def download_file_from_s3(bucket: str, filename: str, local_path: str):
    """
    Generic download helper for s3. Could be moved over to helpers folder...
    This function downloads a file from an S3 bucket to a local path.
    """
    # Set up the S3 client
    if app.config['S3_ENDPOINT'] and MINIO_HOST in app.config['S3_ENDPOINT']:
        s3_url = app.config['S3_ENDPOINT']
        access_key = app.config['AWS_ACCESS_KEY_ID']
        secret_key = app.config['AWS_SECRET_ACCESS_KEY']
        region = app.config['AWS_DEFAULT_REGION']
        secure = s3_url and s3_url.startswith('https')
        s3_client = boto3.client('s3',
                                 endpoint_url=s3_url,
                                 aws_access_key_id=access_key,
                                 aws_secret_access_key=secret_key,
                                 config=Config(signature_version='s3v4'),
                                 region_name=region,
                                 use_ssl=secure)
    else:
        s3_client = boto3.client('s3')
    # Extract the file name from the S3 file path
    tmk_file = filename.split('/')[-1]
    # Specify the full path to save the file
    try:
        s3_client.download_file(bucket, tmk_file, local_path)
        app.logger.info(f'Successfully downloaded file {tmk_file} from S3 bucket.')
    except Exception as e:
        ErrorLog.notify(e, {"bucket": bucket, "filename": filename, "local_path": local_path, "tmk_file": tmk_file})
        app.logger.error(f'Failed to download file {tmk_file} from S3 bucket: {e}')
        raise e

