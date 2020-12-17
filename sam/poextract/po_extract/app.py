import json

import boto3
from rich import print
import requests
import os
from collections import OrderedDict
import time
import numpy as np
import pandas as pd

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

def extract_tables(resp):
    """
    Returns a list of tables as pandas dataframes
    """
    if 'Blocks' not in resp.keys():
        return(None)
    tables = list(filter(lambda x: x['BlockType'] == 'TABLE', resp['Blocks']))
    blockmap = {}
    for b in resp['Blocks']:
        blockmap[b['Id']] = b

    t_unwrap = []
    for t in tables:
 
        # cells = list(filter(lambda x: x['BlockType'] == 'CELL', resp['Blocks']))
        cell_rels = t['Relationships']
        cell_child_rels = list(filter(lambda x: x['Type'] == 'CHILD', cell_rels))
        cell_ids = []
        for cr in cell_child_rels:
            cell_ids = cell_ids + cr['Ids']

        cells = [blockmap[c_id] for c_id in cell_ids]
        max_row_index = max([x['RowIndex'] for x in cells])
        min_row_index = min([x['RowIndex'] for x in cells])
        max_col_index = max([x['ColumnIndex'] for x in cells])
        min_col_index = min([x['ColumnIndex'] for x in cells])        

        df = pd.DataFrame(np.empty((max_row_index,max_col_index),dtype=object))
        for cell in cells:
            if 'Relationships' in cell.keys():
                rels = cell['Relationships']
                child_rels = list(filter(lambda x: x['Type'] == 'CHILD', rels))
                cell_words = []
                for c in child_rels:
                    chs = c['Ids']
                    for child_id in chs:
                        bmx = blockmap[child_id]
                        if bmx['BlockType'] == 'WORD':
                            cell_words.append(bmx['Text'])

                pd_row = cell['RowIndex'] - 1
                pd_col = cell['ColumnIndex'] - 1       
                df.loc[pd_row, pd_col] = " ".join(cell_words)
                
        t_unwrap.append(df)
    return(t_unwrap)

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
    

def flow(event, textract, cache = False):
    # fpath = download_file_to_tmp(s3, event['s3_bucket_name'], event['s3_key_name'], cache = cache)
    recs = process_file(event, textract)
    rval = { "JobStatus" : recs['JobStatus'],
             "tables"    : None }
    if recs['JobStatus'] == 'SUCCEEDED':
        ptables = extract_tables(recs)
        json_t  = lambda x: x.to_json(orient='records')
        jtables = [json_t(t) for t in ptables]
        j2 = []
        for j in jtables:
            j2.append(json.loads(j))
        rval['tables'] = j2
        rval['proc_tables'] = coalesce_tables(rval['tables'])
    return(rval)


def coalesce_tables(tables):
    """ 
    This is from the "tables" collection in recs
    """
    ## For each table, we can:
    ## Process the names in the first row, as column names
    ## If we have a "quantity" column, convert this from euro style to float

    ## If the column names are the same, we can append one to the other.
    
    proc_tables = OrderedDict()
    most_recent_key = None
    for tn,t in enumerate(tables):
        for i, r in enumerate(t):
            ##print(f"Table {tn}, Row number {i}")
            col_accessors = [str(x) for x in range(len(r))]
            ## Get the processed row names
            if i == 0:                
                cnames = {}
                for c in col_accessors:
                    cnames[c] = r[c].lower().strip().replace(" ", "")
                continue
            ## Now, cnames was defined from iteration i==0
            rec = {}
            for c in col_accessors:
                rec[cnames[c]] = r[c]

            fixweight = lambda x: float(x.replace(",", "."))
            
            
            if 'netweight' in rec.keys():
                if rec['netweight'] is not None:
                    rec['netweight'] = fixweight(rec['netweight'])

            if rec['no.'] is not None:
                ## new record
                most_recent_key = rec['no.']
                proc_tables[most_recent_key] = rec
            else:
                ## append the description to previous
                if rec['description'] is not None:
                    proc_tables[most_recent_key]['description'] = proc_tables[most_recent_key]['description'] + " " + rec['description']


    return(list(proc_tables.values()))

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

    event_body = json.loads(event['body'])
    print("EVENT:")
    print(event_body)


    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e

    recs = flow(event_body, textract, cache = True)
    rval = {
        "statusCode": 200,
        "body": json.dumps({
            "message"  : "hello world",
            "textract" : recs
            # "location": ip.text.replace("\n", "")
        }),
    }

    return rval

if __name__ == "__main__":
    event_outer = {"body" : json.dumps( {
        "s3_bucket_name": "po-extract-ingresspos3bucket-14xl4r5co34p1",
        "s3_key_name": "incoming/faktura-117044.pdf",
        "graphql_api_endpoint": "ABCDEF",
        "graphql_api_key": "a1b2c3"
    })}
                                  
    event = json.loads(event_outer["body"])
    print("Running locally")
    session = boto3.Session(profile_name='bredal2')
    s3 = session.client('s3')
    textract = boto3.client('textract')
    recs = flow(event, textract, cache = True)
    print(recs)



    
