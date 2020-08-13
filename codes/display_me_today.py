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

initial_amount=5000000/777.18

# ponderacion del portafolio
ponderacion={'ETHO':4.06/100,
'ESGV':4.12/100,
'VT':12.16/100,
'XLK':15.16/100,
'VTI':19.61/100,
'IVV':11.42/100,
'QQQ':15.30/100,
'ESGU':4.79/100,
'SMH':6.72/100,
'ARKW':2.30/100,
'ARKK':2.13/100,
'OTROS':2.23/100}

# portafolio en el que se invierte
tickers=["ESGV","ETHO","VT","XLK","VTI","IVV","QQQ","SMH","ARKW","ARKK","ESGU"]

dataframes=[]
for i in tickers:
    try:
        # Generamos el diccionario pada cada ticker
        string="{i}=ticker('{i}')".format(i=i)
        exec(string)
        
        string2="df_{i}={i}.getLatest()".format(i=i)
        exec(string2)
        
        string3="df_{i}['ticker']='{i}'".format(i=i)
        exec(string3)
        
        string4="dataframes.append(df_{i})".format(i=i)
        exec(string4)
    except:
        pass

# Concatenamos todos los dataframes en solo uno
day_display=reduce(lambda x, y: pd.concat([x, y]), dataframes)

print("Getting results...")

# agregamos una columna de ponderacion de cada instrumento
day_display["pond"]=day_display["ticker"].apply(lambda x: ponderacion.get(x))

# Extraemos los montos que no tuvieron pnderacion
not_considered_per=1-sum(day_display["pond"])

# Guardamos lo que no se invirtio.. no se considera en la estimacion
rest=initial_amount*not_considered_per
invested=initial_amount-rest

# Agregamos columnas de cantidad inicial invertida y no invertida independiente del fondo
day_display["initial_invested_usd"]=initial_amount
day_display["real_invested"]=invested
day_display["not_invested"]=rest

# Calculamos lo que se invirtio en cada instrumento
day_display["invested"]=day_display["pond"].apply(lambda x: x*initial_amount)

# Calculamos las ganancias o perdidas
day_display["profit"]=(day_display["change"]/100)*(day_display["invested"])

# Calculamos el nuevo valor de la cantidad invertida en el instrumento 
day_display["estimated"]=day_display["invested"]+day_display["profit"]

# Agregamos una columna con el resultado final de lo invertido
day_display['total_result']=sum(day_display["estimated"])-sum(day_display["invested"])

print("Saving...")

save_gsheets(0,day_display)

print("Process completed")
