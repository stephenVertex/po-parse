import json
import tabula
import boto3
from rich import print
import requests
import os
from collections import OrderedDict

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


def process_file(fpath):
    TBL_TOP  = 300
    TBL_LEFT = 50
    TBL_BOT  = 720
    TBL_RT   = 464


    ## Define the area of the PDF we want to read
    x = tabula.read_pdf(fpath,
                        area = (TBL_TOP, TBL_LEFT, TBL_BOT, TBL_RT),
                        pages="all")

    ## How to transform the column names
    kv_mapper = {'No.'         : 'po_num',
                 'Description' : 'descr',
                 'Weight'      : 'weight',
                 'y'           : 'qty'
                 }


    ## How to process the values
    identity = lambda x : x
    transformers = {
        'No.'         : lambda x: str(int(x)),
        'Description' : identity,
        'Weight'      : lambda x: float(x.replace(",", ".")),
        'y'           : int
    }


    ## Extract the results from each page
    most_recent_key = None
    my_order = OrderedDict()
    for i, page in enumerate(x):
        print("################################################################################")
        print(f"Processing invoice page {i}")

        ## if we didn't get column names, then bump up the range
        ## NEED A SPECIAL ROUTINE TO MOVE THE FRAME AROUND HERE
        ## THE CONDITION THAT WE WANT IS TO HAVE EXACTLY 4
        ## WE NEED A FUNCTION THAT WILL CONTINUE TO LOOP UNTIL EITHER THE BOTTOM IS TOO CLOSE TO THE TOP
        ## OR WE GET WHAT WE WANT
        if (page.columns[0] != "No."):
            x2 = tabula.read_pdf(fpath, area = (TBL_TOP - 5, TBL_LEFT, TBL_BOT-350, TBL_RT), pages=(i+1))
            page = x2[0]

        records = json.loads(page.to_json(orient='records'))
        for rec in records:

            new_rec = {}
            for k,v in rec.items():
                f = transformers[k]
                if v is not None:
                    new_rec[kv_mapper[k]] = f(v)
                else:
                    new_rec[kv_mapper[k]] = None


            if new_rec['po_num'] is not None:
                ## We are at a new record
                print("\n----------------------------------------\n")
                print(f"Beginning PO: {new_rec['po_num']}")
                most_recent_key = new_rec['po_num']
                my_order[most_recent_key] = new_rec
                print(f"\t{new_rec['descr']}")

            else:
                ## We are continuing an old record            
                print(f"\t+ {new_rec['descr']} to PO {most_recent_key}")
                my_order[most_recent_key]['descr'] = my_order[most_recent_key]['descr'] + " " + new_rec['descr']
    return(my_order)


def flow(event, s3):
    fpath = download_file_to_tmp(s3, event['s3_bucket_name'], event['s3_key_name'])
    recs = process_file(fpath)
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


    recs = flow(event, s3)
    print(recs)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }



    
if __name__ == "__main__":
    event = {
        's3_bucket_name': 'po-parse-2-ingresss3bucket2-yi5e579i9uoo',
        's3_key_name': 'incoming/faktura-117044.pdf',
        'graphql_api_endpoint': 'ABCDEF',
        'graphql_api_key': 'a1b2c3'
    }

    session = boto3.Session(profile_name='bredal2')
    s3 = session.client('s3')
    recs = flow(event, s3)
    print(recs)



    
