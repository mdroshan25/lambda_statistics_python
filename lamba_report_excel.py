import boto3, sys
from datetime import datetime, timedelta
import csv

from pandas.tests.io.excel.test_xlsxwriter import xlsxwriter


class Lambda_Statistics() :
    # Class variable
    maxval = 0
    # next_token = ''
    starttime = datetime.utcnow() - timedelta(days=1)
    endtime = datetime.utcnow()

    # Generate Excel Sheet Start
    # workbook = xlsxwriter.Workbook("report.xlsx")

    def convert_to_csv(self, cost_metrics) :
        with open("/tmp/report.csv", "w+") as cost_report :
            csvWriter = csv.writer(cost_report, delimiter=',')
        csvWriter.writerows(cost_metrics)

    def create_handler(self, service) :
        return boto3.client(service, 'us-east-1')

    def getmetricdata(self, client, **event) :
        if event.get('NextToken') is None or event.get('NextToken') == '' :
            return client.get_metric_data(MetricDataQueries=
                                          event.get("MetricDataQueries"),
                                          StartTime=event.get("StartTime"),
                                          EndTime=event.get("EndTime"),
                                          MaxDatapoints=5000
                                          )
        else :
            return client.get_metric_data(MetricDataQueries=
                                          event.get("MetricDataQueries"),
                                          StartTime=event.get("StartTime"),
                                          EndTime=event.get("EndTime"),
                                          NextToken=event.get("NextToken"),
                                          MaxDatapoints=5000
                                          )

    def list_functions(self, lambada_hd) :

        paginator = lambada_hd.get_paginator('list_functions')

        for page in paginator.paginate() :
            for function_name in page['Functions'] :
                yield function_name['FunctionName']

    def list_metrics(self) :
        lambada_hd = self.create_handler('lambda')
        client = self.create_handler('cloudwatch')
        for lambda_function in self.list_functions(lambada_hd) :
            results = self.getmetricdata(
                client,
                MetricDataQueries=[
                    {
                        'Id' : 'invocations',
                        'MetricStat' : {
                            'Metric' : {
                                'Namespace' : 'AWS/Lambda',
                                'MetricName' : 'Invocations',
                                'Dimensions' : [
                                    {
                                        'Name' : 'FunctionName',
                                        'Value' : lambda_function
                                    },
                                ]
                            },
                            'Period' : 60,
                            'Stat' : 'Sum',
                            'Unit' : 'Count'
                        },
                        'Label' : 'Invocations',
                        'ReturnData' : True
                    },
                    {
                        'Id' : 'errors',
                        'MetricStat' : {
                            'Metric' : {
                                'Namespace' : 'AWS/Lambda',
                                'MetricName' : 'Errors',
                                'Dimensions' : [
                                    {
                                        'Name' : 'FunctionName',
                                        'Value' : lambda_function
                                    },
                                ]
                            },
                            'Period' : 60,
                            'Stat' : 'Sum',
                            'Unit' : 'Count'
                        },
                        'Label' : 'Errors',
                        'ReturnData' : True
                    },
                    {
                        'Id' : 'duration',
                        'MetricStat' : {
                            'Metric' : {
                                'Namespace' : 'AWS/Lambda',
                                'MetricName' : 'Duration',
                                'Dimensions' : [
                                    {
                                        'Name' : 'FunctionName',
                                        'Value' : lambda_function
                                    },
                                ]
                            },
                            'Period' : 60,
                            'Stat' : 'Average',
                            'Unit' : 'Milliseconds'
                        },
                        'Label' : 'Duration',
                        'ReturnData' : True
                    }
                ],
                StartTime=self.starttime,
                EndTime=self.endtime,
                ScanBy='TimestampDescending',
                NextToken=''
            )
            # print(results, lambda_function)
            yield (results, lambda_function)

    def display_results(self) :
        cost_metrics = list()
        print('{:<60} | {:<20} | {:<11} | {:<14} | {:<17}'.format(
            'Function Name', 'Invocations', 'Errors', 'Duration (sec)',
            'Concurrency (est)')
        )
        print('-' * 159)
        list_metrics = self.list_metrics()

        for each_item in list_metrics :
            if each_item[0]['MetricDataResults'][0]['Timestamps'] :
                # for i in range(len(each_item[0]['MetricDataResults'][0]['Timestamps'])):
                print('{:<80}  | {:<25} | {:>11.3f} | {:>14.2f} | {:>17.1f}'.format(
                    each_item[1],
                    str(sum(each_item[0]['MetricDataResults'][0]['Values'])),
                    sum(each_item[0]['MetricDataResults'][1]['Values']),
                    sum(each_item[0]['MetricDataResults'][2]['Values']) / 1000,
                    round(sum(each_item[0]['MetricDataResults'][0]['Values']) / 60 * sum(
                        each_item[0]['MetricDataResults'][1]['Values']) / 1000)
                )
                )
                cost_metrics.append([each_item[1], str(
                    sum(each_item[0]['MetricDataResults'][0]['Values'])),
                                     sum(each_item[0]['MetricDataResults'][1]['Values']),
                                     sum(each_item[0]['MetricDataResults'][2][
                                             'Values']) / 1000, round(
                        sum(each_item[0]['MetricDataResults'][0]['Values']) / 60 * sum(
                            each_item[0]['MetricDataResults'][1]['Values']) / 1000)])
            else :
                print('{:<80} | {:<25} | {:<11} | {:<14} | {:<17}'.format(each_item[1],
                                                                          'No Data', '',
                                                                          '', ''))
                cost_metrics.append([each_item[1], 'No Data', '', '', ''])

            if each_item[0]['MetricDataResults'][0]['StatusCode'] == 'PartialData' :
                next_token = each_item[0]['NextToken']
            else :
                next_token = None
        # Save the cost metric data to CSV file

        fields = [["Function Name", "Invocations", "Errors", "Duration (sec)",
                   "Concurrency (est)"]]

        with open("report1.csv", "w+") as cost_report :

            csvWriter = csv.writer(cost_report, dialect='excel')
            csvWriter.writerows(fields)
            csvWriter.writerows((cost_metrics))


# Create the handler and execute the results

a = Lambda_Statistics()
a.display_results()
