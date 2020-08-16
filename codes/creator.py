import yfinance as yf
import requests
import pandas as pd
import datetime as dt
import time
from datetime import timedelta
from prod.model import *
from functools import reduce
from yahoo_fin import stock_info as si
import numpy as np
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import pygsheets

gc = pygsheets.authorize(service_file='key.json')

#open the google spreadsheet 
sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1HOLOArAJ7itQALLOE4Gvn63qwPscZU-_5wyHyTU0GHw/edit#gid=0')

#select the first sheet 
wks = sh[0]

data=wks.get_as_df(has_header=True, index_column=None, start=0, end=None,)
data["perc"]=data["usd"].apply(lambda x: x/sum(data["usd"]))
data["date"]=dt.date.today()

data.to_json("../data/purchase.json")

wks=sh[1]

data=wks.get_as_df(has_header=True, index_column=None, start=0, end=None,)
data["date"]=dt.date.today()
data.to_json("../data/purchase_etf.json")