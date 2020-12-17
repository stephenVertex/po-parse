#!/usr/bin/env python3

import boto3
import argparse
import logging
from botocore.exceptions import ClientError
import requests
from rich import print
from rich.console import Console
from rich.table import Table

BUCKET   = "po-extract-ingresspos3bucket-14xl4r5co34p1"
ENDPOINT = "https://7yjbo3g1eh.execute-api.ap-southeast-2.amazonaws.com/Prod/po_extract"

def mkTable(proc_table):
    table = Table(show_header = True, header_style = "bold magenta")
    cols = ['no.', 'description', 'quantity', 'netweight']
    for c in cols:
        table.add_column(c)
    for r in proc_table:
        arg_list = []
        for c in cols:
            arg_list.append(str(r[c]))
        table.add_row(*arg_list)
    return(table)

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
    jval = {
        "s3_bucket_name" : BUCKET,
        "s3_key_name"    : S3_KEY_NAME
    }
        
    r = requests.post(ENDPOINT, json = jval)
    proc_table = r.json()['textract']['proc_tables']

    ## STEP 3, Print the table
    console = Console()
    tab = mkTable(proc_table)
    console.print(tab)
    
    
