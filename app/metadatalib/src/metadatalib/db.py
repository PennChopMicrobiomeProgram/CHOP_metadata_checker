import boto3
import datetime
from boto3.dynamodb.conditions import Key, Attr

class MetadataDB(object):
    def __init__(self, bucket: str, project_table: str, submission_table: str) -> bool:
        self.bucket = bucket
        self.client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.project_table = self.dynamodb.Table(project_table)
        self.submission_table = self.dynamodb.Table(submission_table)
    
    def code_exists_s3(self, code: str) -> bool:
        response = self.client.list_objects(Bucket=self.bucket, Delimiter='/')
        for o in response['CommonPrefixes']:
            if o['Prefix'].strip('/') == code:
                return True
        return False
    
    def code_exists(self, code: str) -> bool:
        response = self.project_table.query(KeyConditionExpression=Key('project_code').eq(code))
        items = response['Items']
        return True if len(items) != 0 else False

    def get_project_info_s3(self, code: str) -> tuple:
        response = self.client.get_object(Bucket=self.bucket, Key=f'{code}/info.csv')
        body = response['Body'].read().decode("utf-8")
        vals_str = body.split('\r\n')[1]
        vals_arr = vals_str.split(',')
        return vals_arr[0], vals_arr[1], vals_arr[2]

    def get_project_info(self, code: str) -> tuple:
        response = self.project_table.query(KeyConditionExpression=Key('project_code').eq(code))
        items = response['Items']
        return items[0]['project_name'], items[0]['client_name'], items[0]['client_email']

    def upload_bytes(self, code: str, file: bytes, partial_fp: str):
        fp = f"{partial_fp}.csv"
        response = self.client.put_object(Body=file, Bucket=self.bucket, Key=fp)

    def upload_comment(self, code: str, comment: str, partial_fp: str):
        fp = f"{partial_fp}_comment.txt"
        response = self.client.put_object(Body=str.encode(comment), Bucket=self.bucket, Key=fp)

    def upload(self, code: str, file_str: str, comment: str):
        response = self.submission_table.put_item(
            Item={
                'submission_id': int(datetime.datetime.now().timestamp() * 1000),
                'project_code': code,
                'metadata': file_str,
                'comment': comment
            }
        )