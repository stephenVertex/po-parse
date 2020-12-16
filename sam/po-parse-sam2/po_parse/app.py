import json
import tabula
import boto3
from rich import print
import requests
import os
s3 = boto3.client('s3')

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


def download_file_to_tmp(s3, bucket, key):
    ## Given a boto s3 client, download to s3
    fname = os.path.split(key)[1]
    tmp_path = f"/tmp/{fname}"
    s3.download_file(bucket, key, tmp_path)
    return(tmp_path)

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
    fpath = download_file_to_tmp(s3, event['s3_bucket_name'], event['s3_key_name'])



    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
