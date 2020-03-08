from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
import requests
import pandas as pd
from pandas.io.json import json_normalize
from io import BytesIO as IO

def index(request):

    if request.method == 'GET':
        return render(request, 'index.html')

    elif request.method == 'POST':
        print('POST')
        fields = [ 'address' ]

        errors = {}
        for field in fields:
            if not request.POST.get(field):
                errors[field] = 'This field is required.'

        if errors:
            return render(
                request,
                'index.html',
                context={ 'errors': errors }
            )

        def algo(address):
            print('algo function')
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
            response['Content-Disposition'] = 'attachment; filename="algo.xlsx"'

            # GET account info
            url_1 = f'https://api.algoexplorer.io/v1/account/{address}'
            account = requests.get(url_1)
            num_of_tx = account.json()['numTxs']

            # Create DataFrame
            algo_df = pd.DataFrame()

            # API only returns 100 transactions per request
            # Sending enough requests to capture all transactions in and out of the address
            for x in range(0, (num_of_tx + 100), 100):

                # Getting transactions based on index number
                url = f'https://api.algoexplorer.io/v1/account/{address}/transactions/from/{x}/to/{x+99}'
                request = requests.get(url)

                # If JSON is not empty, DataFrame containing most recent transactions created.
                # Concatenating it main algo_df DataFrame.
                if request.json():
                    df = json_normalize(request.json())
                    algo_df = pd.concat([algo_df, df], sort=False)

            # Wrangle data into human readable format
            algo_df['timestamp'] = pd.to_datetime(algo_df['timestamp'],unit='s')
            algo_df['amount'] = (algo_df['amount'] / 1000000)

            # Reorder for relevance
            algo_df = algo_df[['index', 'amount', 'to', 'from', 'timestamp', 'fee', 'txid', 'type', 'balance', 'toBalance', 'firstRound',
                               'lastRound', 'assetID', 'fromIndex', 'assetIndex', 'fromBalance', 'round','accumulatedFromRewards', 'toIndex',
                               'toRewards', 'accumulatedToRewards', 'globalIndex', 'rewards', 'fromRewards', 'noteb64']]

            # Selecting inbout / outbound transactions 2019
            inbound_2019 = algo_df[(algo_df['timestamp'].dt.year == 2019) & (algo_df['to'] == f"{address}")].reset_index(drop=True)
            outbound_2019 = algo_df[(algo_df['timestamp'].dt.year == 2019) & (algo_df['to'] != f"{address}")].reset_index(drop=True)

            # Selecting inbout / outbound transactions 2020
            inbound_2020 = algo_df[(algo_df['timestamp'].dt.year == 2020) & (algo_df['to'] == f"{address}")].reset_index(drop=True)
            outbound_2020 = algo_df[(algo_df['timestamp'].dt.year == 2020) & (algo_df['to'] != f"{address}")].reset_index(drop=True)

            with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                inbound_2019.to_excel(writer, sheet_name='2019-RECEIVE')
                outbound_2019.to_excel(writer, sheet_name='2019-SEND')
                inbound_2020.to_excel(writer, sheet_name='2020-RECEIVE')
                outbound_2020.to_excel(writer, sheet_name='2020-SEND')

                return response

        print('algo initiated')
        return algo(request.POST.get('address'))
