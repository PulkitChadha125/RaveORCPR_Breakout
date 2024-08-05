import datetime
from SmartApi.smartExceptions import DataException
import SmartApi
import pandas as pd
import requests
from SmartApi import SmartConnect #or from SmartApi.smartConnect import SmartConnect
import pyotp
from logzero import logger
import pandas_ta as ta

apikey="Sg2W3HFf"
secret="9e400a02-cf6a-4e03-887e-a436f413cd36"
USERNAME="S60612177"
PASSWORD="Akki123@"
totp_string="D45IFKPPHUFT3OHK7OAWMSLUCA"
pin = "1234"
smartApi=None


def login(api_key,username,pwd,totp_string):
    global smartApi
    print("login initiated")
    api_key = api_key
    username = username
    pwd = pwd
    smartApi = SmartConnect(api_key)
    try:
        token =totp_string
        totp = pyotp.TOTP(token).now()
    except Exception as e:
        logger.error("Invalid Token: The provided token is not valid.")
        raise e

    correlation_id = "abcde"
    data = smartApi.generateSession(username, pwd, totp)

    if data['status'] == False:
        logger.error(data)

    else:
        authToken = data['data']['jwtToken']

        refreshToken = data['data']['refreshToken']
        feedToken = smartApi.getfeedToken()

        res = smartApi.getProfile(refreshToken)
        smartApi.generateToken(refreshToken)
        res = res['data']['exchanges']

        print(smartApi.getProfile(refreshToken))


def get_ltp(segment,symbol,token):
    global smartApi
    res=smartApi.ltpData(segment,symbol,token)
    ltp_value = res['data']['ltp']
    return ltp_value

def symbolmpping():
    print("Symbol mapping ")
    url="https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    d=requests.get(url).json()
    print("d: ",d)
    tokendf=pd.DataFrame.from_dict(d)
    tokendf['expiry']=pd.to_datetime(tokendf['expiry'])
    tokendf=tokendf.astype({'strike':float})
    print("instrument file generation")
    tokendf.to_csv("Instrument.csv")

def get_historical_data_atr(symbol, token, timeframe, segment,atr):
    global smartApi
    try:
        historicParam = {
            "exchange": segment,
            "symboltoken": token,
            "interval": timeframe,
            "fromdate": "2024-07-08 09:00",
            "todate": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        }
        res = smartApi.getCandleData(historicParam)
        df = pd.DataFrame(res['data'], columns=['date', 'open', 'high', 'low', 'close', 'flag'])

        df['ATR']=ta.atr(high=df['high'],low=df['low'],close=df['close'],length=atr)
        df['date'] = pd.to_datetime(df['date'])
        df.to_csv("data.csv")
        return df

    except Exception as e:
        logger.exception(f"Historic Api failed: {e}")
def get_historical_data(symbol, token, timeframe, segment):
    global smartApi
    try:
        historicParam = {
            "exchange": segment,
            "symboltoken": token,
            "interval": timeframe,
            "fromdate": "2024-02-08 09:00",
            "todate": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        }
        res = smartApi.getCandleData(historicParam)
        df = pd.DataFrame(res['data'], columns=['date', 'open', 'high', 'low', 'close', 'flag'])

        df['date'] = pd.to_datetime(df['date'])
        df.to_csv("data.csv")
        return df

    except Exception as e:
        logger.exception(f"Historic Api failed: {e}")

def buy(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "BUY",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error",e)
        logger.error(f"Order placement failed: {e}")
        print(e)

def sell(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "SELL",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error", e)
        logger.error(f"Order placement failed: {e}")
        print(e)


def SHORT(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "SELL",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error", e)
        logger.error(f"Order placement failed: {e}")
        print(e)


def cover(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "BUY",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error", e)
        logger.error(f"Order placement failed: {e}")
        print(e)
