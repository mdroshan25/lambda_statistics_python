import boto3
from datetime import datetime, timedelta
import json
import requests
import os

#Cloud Watch
cloudwatch = boto3.resource('cloudwatch', region_name='us-east-1')
metric = cloudwatch.Metric('AWS/Billing', 'EstimatedCharges')

#Calculate Date Time
d0 = datetime.now() - timedelta(days=1)
d30 = datetime.now() - timedelta(days=30)
d90 = datetime.now() - timedelta(days=90)
d1 = datetime.now()

start_time = datetime(d0.year, d0.month, d0.day, d0.hour, 0, 0)
month_start_time = datetime(d30.year, d30.month, d30.day, d30.hour, 0, 0)
quarter_start_time = datetime(d90.year, d90.month, d90.day, d90.hour, 0, 0)
day_end_time = datetime(d1.year, d1.month, d1.day, d1.hour, 0, 0)

#print('datefrom_today :', start_time)
#print('datefrom_month :', month_start_time)
#print('datefrom_quarter :', quarter_start_time)
#print('todate :', day_end_time)

#Calculation Per day
response_per_day = metric.get_statistics(
    Dimensions=[
        {
            'Name': 'Currency',
            'Value': 'USD'
        },
    ],
    StartTime=start_time,
    EndTime=day_end_time,
    Period=86400,
    Statistics=[
        'Maximum',
    ]
)
bill_max_day = response_per_day['Datapoints'][0]['Maximum']
#Calculation Per Month
response_per_month = metric.get_statistics(
    Dimensions=[
        {
            'Name': 'Currency',
            'Value': 'USD'
        },
    ],
    StartTime=month_start_time,
    EndTime=day_end_time,
    Period=86400,
    Statistics=[
        'Maximum',
    ]
)
bill_max_month = response_per_month['Datapoints'][0]['Maximum']
#Calculation Per Quarter
response_per_quarter = metric.get_statistics(
    Dimensions=[
        {
            'Name': 'Currency',
            'Value': 'USD'
        },
    ],
    StartTime=quarter_start_time,
    EndTime=day_end_time,
    Period=86400,
    Statistics=[
        'Maximum',
    ]
)
bill_max_quarter = response_per_quarter['Datapoints'][0]['Maximum']

content_day = format(round(bill_max_day,2), '.2f') + 'USD' + ' (Max: from ' + str(start_time) + ' to ' + str(day_end_time) + ') '
content_month = format(round(bill_max_month,2), '.2f') + 'USD' + ' (Max: from ' + str(month_start_time) + ' to ' + str(day_end_time) + ') '
content_quarter = format(round(bill_max_quarter,2), '.2f') + 'USD' + ' (Max: from ' + str(quarter_start_time) + ' to ' + str(day_end_time) + ') '

#print("response per day", response_per_day)

print("BILL Max per day::", bill_max_day)
print("BILL Max per month::", bill_max_month)
print(f"BILL Max per quarter::{bill_max_quarter} \n")

print("content per day::", content_day)
print("content per month::", content_month)
print("content per quarter::", content_quarter)

