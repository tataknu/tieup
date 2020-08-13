def prev_weekday(adate):
    
    from yahoo_fin.stock_info import get_data
    import time    
    from datetime import timedelta
    import datetime as dt
    import yahoo_fin.stock_info as si
    import pandas as pd
    import numpy as np
    #https://stackoverflow.com/questions/12053633/previous-weekday-in-python
    adate -= timedelta(days=1)
    while adate.weekday() > 4: # Mon-Fri are 0-4
        adate -= timedelta(days=1)
    return adate

def check_week():

    from yahoo_fin.stock_info import get_data
    import time    
    from datetime import timedelta
    import datetime as dt
    import yahoo_fin.stock_info as si
    import pandas as pd
    import numpy as np

    todaysDate = dt.date.today()
    date_today=todaysDate.weekday()

    if date_today in range(0,4):
        todaysDate = dt.date.today()
    else:
        todaysDate=prev_weekday(todaysDate)

    yesterday = todaysDate - timedelta(days = 1)
    yesterday = yesterday.weekday()

    if yesterday in range(1,5):
        yesterday = todaysDate - timedelta(days = 1)
    else:
        yesterday=prev_weekday(todaysDate)
    
    response={"today":todaysDate,"yesterday":yesterday}
    
    return(response)

class ticker:
    
    def __init__(self, ticker):
        
        import time    
        from datetime import timedelta
        import datetime as dt

        # Validamos que el dia de ejecucion sea valido
        self.todaysDate=check_week()["today"]
        self.yesterday=check_week()["yesterday"]
        self.today=self.todaysDate.strftime('%m/%d/%Y')
        
        self.name=ticker

        print(self.today)
        print("Creating ticker ...")
    
    def getLatest(self):

        from yahoo_fin.stock_info import get_data
        import time    
        from datetime import timedelta
        import datetime as dt
        import yahoo_fin.stock_info as si
        import requests
        import pandas as pd
        
        # Obtenemos los ultimos registros para el dia actual
        try:

            data=get_data(self.name , start_date = self.today)
            print(str(self.name) + str(" was created, date:") + str(self.today) )
            
            # Obtenemos ultimo precio dsiponible para el instrumento
            data["last_price"]=si.get_live_price(self.name)
            
            # Seleccionamos los campos y reiniciamos el indice
            data=data[["open","high","low","last_price"]].reset_index()        
            data = data.rename(columns={'index':'date'})
            
            # Hacemos calculo de variacion respecto a la apertura
            data["change"]=((data["last_price"]/data["open"])-1)*100
            data["price_change"]=data["last_price"]-data["open"]


        except:

            site=build_url(self.name)
            resp = requests.get(site)
            data = resp.json()

            temp_time=data['chart']['result'][0]['timestamp']
            date=pd.to_datetime(temp_time, unit = "s")[0]
            latest_price=data['chart']['result'][0]['meta']['regularMarketPrice']
            open_price=data['chart']['result'][0]['indicators']['quote'][0]['open'][0]
            high=data['chart']['result'][0]['indicators']['quote'][0]['high']
            high=getLatestHigh(high)
            low=data['chart']['result'][0]['indicators']['quote'][0]['low']
            low=getLatestLow(low)
            actual={'date':date,'open':open_price,'high':high,'low':low,'last_price':latest_price}
            data=pd.DataFrame(data=actual,index=[0])

            # Hacemos calculo de variacion respecto a la apertura
            data["change"]=((data["last_price"]/data["open"])-1)*100
            data["price_change"]=data["last_price"]-data["open"]
        
        return(data)
    
    def getDays(self,i):

        from yahoo_fin.stock_info import get_data
        import time    
        from datetime import timedelta
        import datetime as dt
        import yahoo_fin.stock_info as si
        import pandas as pd
        import numpy as np
        
        self.daysAgo = self.todaysDate - timedelta(days = i)
        data = get_data(self.name , start_date = self.daysAgo, end_date= self.today)
        data = data.reset_index()
        data = data.rename(columns={'index':'date'})

        data_day = get_data(self.name , start_date = self.today)
        
        date = dt.datetime.strptime(self.today, "%m/%d/%Y")
        
        data_day["date"] = date
        
        data=pd.concat([data, data_day],ignore_index=True)
        
        return(data)
    
    def getWeeks(self,i):

        from yahoo_fin.stock_info import get_data
        import time    
        from datetime import timedelta
        import datetime as dt
        import yahoo_fin.stock_info as si
        import pandas as pd
        import numpy as np
        
        self.daysAgo = self.todaysDate - timedelta(weeks = i)
        data = get_data(self.name , start_date = self.daysAgo, end_date= self.today)
        data = data.reset_index()
        data = data.rename(columns={'index':'date'}) 

        data_day = get_data(self.name , start_date = self.today)
        
        date = dt.datetime.strptime(self.today, "%m/%d/%Y")
        
        data_day["date"] = date
        
        data=pd.concat([data, data_day],ignore_index=True)
        
        return(data)


def build_url(ticker):
    
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
    
    site = base_url + ticker

    return site

def getLatestHigh(prices):
    a=[]
    for i in prices:
        try:
            a.append(float(i))
        except:
            continue
    return(max(a))

def getLatestLow(prices):
    a=[]
    for i in prices:
        try:
            a.append(float(i))
        except:
            continue
    return(min(a))

def save_gsheets(page,dataframe):

    import gspread
    import pandas as pd
    from oauth2client.service_account import ServiceAccountCredentials
    import pygsheets

    gc = pygsheets.authorize(service_file='key.json')

    #open the google spreadsheet 
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1z7zzHgM6t4ySUkPZe5BdFsBvTD6RxsfSdKEnqWU1a2Q/edit#gid=67598709')

    #select the first sheet 
    wks = sh[page]

    #update the first sheet with df, starting at cell B2. 
    wks.set_dataframe(dataframe, 'A1')
