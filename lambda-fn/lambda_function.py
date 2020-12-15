import json
import urllib.parse
import boto3
import tabula
import os
from collections import OrderedDict

print('Loading function')

s3 = boto3.client('s3')


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


def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        print("Attempting to get the following object:")
        print(f"s3://{bucket}/{key}")
        response = s3.get_object(Bucket=bucket, Key=key)

        ################################################################################
        ## HERE IS THE MAIN FUNCTION BODY.
        ## WE NEED TO DO THE FOLLOWING:
        

        fpath = download_file_to_tmp(s3, bucket, key)
        records = process_file(fpath)

        ################################################################################

        print("CONTENT TYPE: " + response['ContentType'])
        return records
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

if __name__ == "__main__":
    print("Running locally")
    
    session = boto3.Session(profile_name='bredal2')
    s3 = session.client('s3')
    
    
    SAMPLE_S3_BUCKET = "bredal-australia-internal"
    SAMPLE_S3_KEY    = "purchase-orders/ingest/faktura-117044.pdf"
    fpath = download_file_to_tmp(s3, SAMPLE_S3_BUCKET, SAMPLE_S3_KEY)
    records = process_file(fpath)
