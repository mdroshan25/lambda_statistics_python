import csv
import os
import sys
from datetime import datetime, timedelta

import boto3

from ecdr_test_monitor_cost.sendmail import send_email
from ecdr_test_monitor_cost.utils import get_logger

log = get_logger()

sender = ""
receiver = ""
smtp_server = "smtp-mail.outlook.com"
smtp_port = "587"
region = "us-east-1"

file_name = "cost_metrics.csv"


class Lambda_Statistics(object):
    # Class variable
    starttime = datetime.utcnow() - timedelta(days=90)
    endtime = datetime.utcnow()

    # Generate Excel Sheet Start

    def create_handler(self, service):
        return boto3.client(service, "us-east-1")

    def getmetricdata(self, client, **event):
        if event.get("NextToken") is None or event.get("NextToken") == "":
            return client.get_metric_data(
                MetricDataQueries=event.get("MetricDataQueries"),
                StartTime=event.get("StartTime"),
                EndTime=event.get("EndTime"),
                MaxDatapoints=5000,
            )
        else:
            return client.get_metric_data(
                MetricDataQueries=event.get("MetricDataQueries"),
                StartTime=event.get("StartTime"),
                EndTime=event.get("EndTime"),
                NextToken=event.get("NextToken"),
                MaxDatapoints=5000,
            )

    def list_functions(self, lambada_hd):

        paginator = lambada_hd.get_paginator("list_functions")

        for page in paginator.paginate():
            for function_name in page["Functions"]:
                yield function_name["FunctionName"]

    def list_metrics(self):
        lambada_hd = self.create_handler("lambda")
        client = self.create_handler("cloudwatch")
        for lambda_function in self.list_functions(lambada_hd):
            results = self.getmetricdata(
                client,
                MetricDataQueries=[
                    {
                        "Id": "invocations",
                        "MetricStat": {
                            "Metric": {
                                "Namespace": "AWS/Lambda",
                                "MetricName": "Invocations",
                                "Dimensions": [
                                    {"Name": "FunctionName", "Value": lambda_function},
                                ],
                            },
                            "Period": 60,
                            "Stat": "Sum",
                            "Unit": "Count",
                        },
                        "Label": "Invocations",
                        "ReturnData": True,
                    },
                    {
                        "Id": "errors",
                        "MetricStat": {
                            "Metric": {
                                "Namespace": "AWS/Lambda",
                                "MetricName": "Errors",
                                "Dimensions": [
                                    {"Name": "FunctionName", "Value": lambda_function},
                                ],
                            },
                            "Period": 60,
                            "Stat": "Sum",
                            "Unit": "Count",
                        },
                        "Label": "Errors",
                        "ReturnData": True,
                    },
                    {
                        "Id": "duration",
                        "MetricStat": {
                            "Metric": {
                                "Namespace": "AWS/Lambda",
                                "MetricName": "Duration",
                                "Dimensions": [
                                    {"Name": "FunctionName", "Value": lambda_function},
                                ],
                            },
                            "Period": 60,
                            "Stat": "Average",
                            "Unit": "Milliseconds",
                        },
                        "Label": "Duration",
                        "ReturnData": True,
                    },
                ],
                StartTime=self.starttime,
                EndTime=self.endtime,
                ScanBy="TimestampDescending",
                NextToken="",
            )

            yield (results, lambda_function)

    def display_results(self):

        try:
            log.info("Start of metrics process")
            print("-" * 159)
            THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
            my_file = os.path.join(THIS_FOLDER, file_name)
            print("-" * 159)
            cost_metrics = list()
            log.info(
                "{:<60} | {:<20} | {:<11} | {:<14} | {:<17}".format(
                    "Function Name",
                    "Invocations",
                    "Errors",
                    "Duration (sec)",
                    "Concurrency (est)",
                )
            )
            log.info("-" * 159)

            list_metrics = self.list_metrics()
            log.info(
                "Calculating metrics info for process, error info, duration and concurrency"
            )
            for each_item in list_metrics:
                if each_item[0]["MetricDataResults"][0]["Timestamps"]:

                    cost_metrics.append(
                        [
                            format(each_item[1]),
                            str(sum(each_item[0]["MetricDataResults"][0]["Values"])),
                            sum(each_item[0]["MetricDataResults"][1]["Values"]),
                            sum(each_item[0]["MetricDataResults"][2]["Values"]) / 1000,
                            round(
                                sum(each_item[0]["MetricDataResults"][0]["Values"])
                                / 60
                                * sum(each_item[0]["MetricDataResults"][1]["Values"])
                                / 1000
                            ),
                        ]
                    )
                else:
                    # log.info("adding info for no information on function")
                    cost_metrics.append([format(each_item[1]), "No Data", "", "", ""])

                if each_item[0]["MetricDataResults"][0]["StatusCode"] == "PartialData":
                    next_token = each_item[0]["NextToken"]
                    # log.info("moving to next function as status is partial data")
                else:
                    # log.info("Nothing to process")
                    next_token = None
            # Save the cost metric data to CSV file
            log.info("Start of Excel generation")
            fields = [
                [
                    "Function Name ",
                    "Invocations ",
                    "Errors ",
                    "Duration (sec) ",
                    "Concurrency (est) ",
                ]
            ]
            with open(my_file, "w+") as cost_report:
                csvWriter = csv.writer(cost_report, dialect="excel")
                csvWriter.writerows(fields)
                csvWriter.writerows((cost_metrics))
            log.info("Excel generation complete")
            log.info("-" * 159)
            log.info("Process start to send email")

            send_email(sender, receiver, smtp_server, smtp_port, my_file)
        except Exception as err:
            log.exception(err)
            raise err


# Create the handler and execute the results
a = Lambda_Statistics()
a.display_results()

