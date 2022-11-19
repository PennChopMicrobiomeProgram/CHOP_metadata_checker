import boto3
import datetime

class MetadataDB(object):
    def __init__(self, bucket: str) -> bool:
        self.bucket = bucket
        self.client = boto3.client('s3')
    
    def code_exists(self, code: str):
        response = self.client.list_objects(Bucket=self.bucket, Delimiter='/')
        for o in response['CommonPrefixes']:
            if o['Prefix'].strip('/') == code:
                return True
        return False

    def get_project_info(self, code: str) -> tuple:
        response = self.client.get_object(Bucket=self.bucket, Key=f'{code}/info.csv')
        body = response['Body'].read().decode("utf-8")
        vals_str = body.split('\r\n')[1]
        vals_arr = vals_str.split(',')
        return vals_arr[0], vals_arr[1], vals_arr[2]


    def upload(self, code: str, file):
        fp = f"{code}/{datetime.datetime.now()}"
        response = self.client.upload_file(file, self.bucket, fp)