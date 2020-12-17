#!/usr/bin/env python3

import boto3
import argparse
import logging
from botocore.exceptions import ClientError


BUCKET = 'po-extract-ingresspos3bucket-14xl4r5co34p1'


def upload_file(s3, file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

if __name__ == "__main__":
    session = boto3.Session(profile_name='bredal2')
    s3 = session.client('s3')

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--invoice-pdf',
                        help='path to pdf file of invoice')
    args = parser.parse_args()
    INVOICE_FILE = args.invoice_pdf
    #INVOICE_FILE = "sample-input-2.pdf"
    print(f"INVOICE FILE: {INVOICE_FILE}")

    ## STEP 1, uploading to S3
    
    S3_KEY_NAME = "incoming/" + INVOICE_FILE
    print(f"s3://{BUCKET}/{S3_KEY_NAME}")
    upload_success = upload_file(s3, INVOICE_FILE, BUCKET, S3_KEY_NAME)
    

    ## STEP 2, POST to API Endpoint

