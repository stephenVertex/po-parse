#!/usr/bin/env python3



import tabula
import pandas
from collections import OrderedDict
import json

TBL_TOP  = 300
TBL_LEFT = 50
TBL_BOT  = 720
TBL_RT   = 464


x = tabula.read_pdf("faktura-117044.pdf",
                    area = (TBL_TOP, TBL_LEFT, TBL_BOT, TBL_RT),
                    pages="all")

kv_mapper = {'No.'         : 'po_num',
             'Description' : 'descr',
             'Weight'      : 'weight',
             'y'           : 'qty'
             }

identity = lambda x : x

transformers = {
    'No.'         : lambda x: str(int(x)),
    'Description' : identity,
    'Weight'      : lambda x: float(x.replace(",", ".")),
    'y'           : int
}



most_recent_key = None
my_order = OrderedDict()
for i, page in enumerate(x):
    print("################################################################################")
    print(f"Processing invoice page {i}")

    ## if we didn't get column names, then bump up the range
    ## NEED A SPECIAL ROUTINE TO MOVE THE FRAME AROUND HERE
    ## THE CONDITION THAT WE WANT IS TO HAVE EXACTLY 4
    if (page.columns[0] != "No."):
        x2 = tabula.read_pdf("faktura-117044.pdf", area = (TBL_TOP - 5, TBL_LEFT, TBL_BOT-350, TBL_RT), pages=(i+1))
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



