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
import os.path
import subprocess

try:
    print("Creating portafolio from google drive...")
    os.system("python3 creator.py")
except:
    print("Unable to create the portafolio")
    print("Please check drive connections")


json=pd.read_json("../Data/purchase_etf.json")

json=json.to_dict('series')
tickers=list(json['tickers'])
perc=list(json['perc'])
tickers=dict(zip(tickers,perc))

json["usd"]=json["usd"].apply(lambda x: (float(x.replace(",","."))))
initial_amount=sum(json["usd"])/len(json['tickers'])

# ponderacion del portafolio
ponderacion=tickers

# portafolio en el que se invierte
tickers=list(ponderacion.keys())

dataframes=[]
for i in tickers:
       
    # Generamos el diccionario pada cada ticker
    string="{i}=ticker('{i}')".format(i=i)
    exec(string)
    
    string2="df_{i}={i}.getLatest()".format(i=i)
    exec(string2)
    
    string3="df_{i}['ticker']='{i}'".format(i=i)
    exec(string3)
    
    string4="dataframes.append(df_{i})".format(i=i)
    exec(string4)

# Concatenamos todos los dataframes en solo uno
day_display=reduce(lambda x, y: pd.concat([x, y]), dataframes)

day_display=day_display.reset_index()

dataframes=[]
dataframes_2=[]
estado=False

for i in tickers:
    
    # Creamos un dataframe para seleccionar los registros por cada ticker
    df2=day_display[day_display['ticker']==i]
    
    # Separamos los tickers que tienen mas de una entrada
    if len(day_display[day_display['ticker']==i])>1:
        dataframes.append(df2)
    else:
        estado=True
        dataframes_2.append(df2)
    
# Juntamos los registros con mas de una entrada
df_with_many_entries=reduce(lambda x, y: pd.concat([x, y]), dataframes)

# Nos quedamos con los ultimos datos de lectura
df_with_many_entries=df_with_many_entries[df_with_many_entries['index']==1]

day_display=df_with_many_entries

# Si vienen resultados repetidos tenemos que juntar los que no venian repetidos
if estado==True:
    # Juntamos los registros con solo una entrada
    df_with_one=reduce(lambda x, y: pd.concat([x, y]), dataframes_2)
    day_display=pd.concat(df_with_many_entries,df_with_one)
else:
    pass

# agregamos una columna de ponderacion de cada instrumento
day_display["pond"]=day_display["ticker"].apply(lambda x: ponderacion.get(x))

day_display["pond"]=day_display["pond"].apply(lambda x: (float(x.replace(",",".")))/100)

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

day_display=day_display.drop(columns=["index"])

print("Saving in google drive...")
save_gsheets(0,day_display)

from datetime import datetime
from pytz import timezone
import json  

tz = timezone('EST')
now_est=datetime.now(tz)
close_time = now_est.replace( hour=16, minute=15, second=0, microsecond=0 )

print("Checking if day is done...")
if close_time<now_est:
    gc = pygsheets.authorize(service_file='key.json')
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1HOLOArAJ7itQALLOE4Gvn63qwPscZU-_5wyHyTU0GHw/edit#gid=0')
    wks = sh[1]
    resultado_dia=sum(day_display["estimated"])+sum(day_display["not_invested"])/len(day_display["not_invested"])
    wks.update_value('C2',resultado_dia, parse=None)


    year=dt.date.today().strftime('%Y')
    month=dt.date.today().strftime('%m')
    day=dt.date.today().strftime('%d')
    today=dt.date.today().strftime('%m%d%Y')

    try:
        print("Checking folders...")
        os.mkdir("../Data/history/"+str(year))
    except:
        pass

    try:
        os.mkdir("../Data/history/"+str(year)+"/"+str(month))
    except:
        pass
    print("Saving the results of the day")
    day_display.to_csv("../Data/history/"+str(year)+"/"+str(month)+"/"+str(today)+".csv",index=False)

else:
    pass
