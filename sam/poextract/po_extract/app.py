import json

import boto3
from rich import print
import requests
import os
from collections import OrderedDict
import time

s3 = boto3.client('s3')
textract = boto3.client('textract')

def getSessionInfo(running_aws = True):
    # CFT Stack Variables
    # OUTPUT_KEYS = ['AmbraStepFunction']  # <-- Use the names set in template.yaml Outputs
    stack_name = 'po-parse-samified'
    stack_output = {}
    if running_aws:
        session = boto3.Session()
    else:
        session = boto3.Session(profile_name='bredal2')
    cf_resource = session.resource('cloudformation')
    stack = cf_resource.Stack(stack_name)
    # Show raw stack outputs from CFT
    print(f'Keys in output_object: {stack.outputs}')    
    # Transform them into a map
    for x in stack.outputs:
        stack_output[x['OutputKey']] = x['OutputValue']
    return(stack_output)


def download_file_to_tmp(s3, bucket, key, cache = False):
    ## Given a boto s3 client, download to s3
    fname = os.path.split(key)[1]
    tmp_path = f"/tmp/{fname}"
    if cache:
        if os.path.exists(tmp_path):
            print(f"Using a local cache. We already have {tmp_path}.")
            return(tmp_path)
    s3.download_file(bucket, key, tmp_path)
    print(f"Downloaded s3://{bucket}/{key} to {tmp_path}")
    return(tmp_path)


def process_file(event, textract):
    bucket   = event['s3_bucket_name']
    document = event['s3_key_name']


    
    a_start = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}},
        FeatureTypes=["TABLES"]
    )


    
    timeout = 300
    for i in range(timeout):
        response2 = textract.get_document_analysis(JobId = a_start['JobId'])
        if response2['JobStatus'] == 'IN_PROGRESS':
            time.sleep(1)
        else:
            print(response2['JobStatus'])
            break

    return(response2)
    

def flow(event, s3, textract, cache = False):
    # fpath = download_file_to_tmp(s3, event['s3_bucket_name'], event['s3_key_name'], cache = cache)
    recs = process_file(fpath, textract)
    return(recs)


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    print("EVENT:")
    print(event)


    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e

    recs = flow(event, s3, textract, cache = True)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message"  : "hello world",
            "textract" : recs
            # "location": ip.text.replace("\n", "")
        }),
    }

if __name__ == "__main__":
    event = {
        's3_bucket_name': 'po-extract-ingresspos3bucket-14xl4r5co34p1',
        's3_key_name': 'incoming/faktura-117044.pdf',
        'graphql_api_endpoint': 'ABCDEF',
        'graphql_api_key': 'a1b2c3'
    }

    print("Running locally")
    session = boto3.Session(profile_name='bredal2')
    s3 = session.client('s3')
    textract = boto3.client('textract')
    recs = flow(event, s3, textract, cache = True)
    print(recs)



    
