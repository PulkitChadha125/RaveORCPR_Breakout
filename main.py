import threading
import requests
import FyresIntegration
import time
import traceback
from datetime import datetime, timedelta
import pandas as pd
result_dict={}
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta

# for buy trade itm means 55400,55300....call
# for sell trade itm means 55400, 55500...put
def getstrikes_put(ltp, step , strikestep):
    result = {}
    result[int(ltp)] = None

    for i in range(step):
        result[int(ltp + strikestep * (i + 1))] = None
    return result

def getstrikes_call(ltp, step , strikestep):
    result = {}
    result[int(ltp)] = None
    for i in range(step):
        result[int(ltp - strikestep * (i + 1))] = None

    return result

def fetchcorrectstrike(strikelist):
    target_value = 0.6
    closest_key = None
    min_difference = float('inf')

    for key, value in strikelist.items():
        if value > target_value and value - target_value < min_difference:
            min_difference = value - target_value
            closest_key = key

    return closest_key
def convert_date_to_short_format(date_string):
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    # Format the datetime object into the desired short format
    short_format = date_obj.strftime("%y%b").upper()  # Convert to uppercase
    return short_format
def convert_julian_date(julian_date):
    input_format = "%y%m%d"
    parsed_date = datetime.strptime(str(julian_date), input_format)
    desired_time = "15:30:00"
    formatted_date_with_time = parsed_date.replace(hour=15, minute=30, second=0)

    return formatted_date_with_time


def get_delta(strikeltp,underlyingprice,strike,timeexpiery,riskfreeinterest,flag):
    # flag me  call  'c' ya put 'p'
    from py_vollib.black_scholes.greeks.analytical import delta
    iv= implied_volatility(price=strikeltp,S=underlyingprice,K=strike,t=timeexpiery,r=riskfreeinterest,flag=flag)
    value = delta(flag,underlyingprice,strike,timeexpiery,riskfreeinterest,iv)
    print("delta",value)
    return value

def option_delta_calculation(symbol,expiery,strike,optiontype,underlyingprice,MODE):
    optionsymbol = f"NSE:{symbol}{expiery}{strike}{optiontype}"
    if symbol == "SENSEX":
        optionsymbol = f"BSE:{symbol}{expiery}{strike}{optiontype}"

    optionltp= FyresIntegration.get_ltp(optionsymbol)
    print("expiery: ",expiery)
    if MODE=="WEEKLY":
        distanceexp=convert_julian_date(expiery)
    if MODE=="MONTHLY":
        distanceexp=expiery
    print("distanceexp: ",distanceexp)
    t= (distanceexp-datetime.now())/timedelta(days=1)/365
    print("t: ",t)
    if optiontype=="CE":
        fg="c"
    else :
        fg = "p"
    print("optionltp: ",optionltp)
    print("underlyingprice: ", underlyingprice)
    print("strike: ", strike)
    value=get_delta(strikeltp=optionltp, underlyingprice=underlyingprice, strike=strike, timeexpiery=t,flag=fg ,riskfreeinterest=0.1)
    return value


def round_down_to_interval(dt, interval_minutes):
    remainder = dt.minute % interval_minutes
    minutes_to_current_boundary = remainder

    rounded_dt = dt - timedelta(minutes=minutes_to_current_boundary)

    rounded_dt = rounded_dt.replace(second=0, microsecond=0)

    return rounded_dt


def determine_min(minstr):
    min = 0
    if minstr == "1":
        min = 1
    if minstr == "3":
        min = 3
    if minstr == "5":
        min = 5
    if minstr == "15":
        min = 15
    if minstr == "30":
        min = 30

    return min

def delete_file_contents(file_name):
    try:
        # Open the file in write mode, which truncates it (deletes contents)
        with open(file_name, 'w') as file:
            file.truncate(0)
        print(f"Contents of {file_name} have been deleted.")
    except FileNotFoundError:
        print(f"File {file_name} not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
def get_user_settings():
    delete_file_contents("OrderLog.txt")
    global result_dict
    # Symbol,lotsize,Stoploss,Target1,Target2,Target3,Target4,Target1Lotsize,Target2Lotsize,Target3Lotsize,Target4Lotsize,BreakEven,ReEntry
    try:
        csv_path = 'TradeSettings.csv'
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        result_dict = {}
        # Symbol,EMA1,EMA2,EMA3,EMA4,lotsize,Stoploss,Target,Tsl
        for index, row in df.iterrows():
            # Create a nested dictionary for each symbol
            symbol_dict = {
                'Symbol': row['Symbol'],"Quantity":row['Quantity'],'EXPIERY':row['EXPIERY'],'TimeFrame':row['TimeFrame'],
                'once' : False,'USE_CPR': row['USE_CPR'],'PartialProfitQty': row['PartialProfitQty'],'Atr_Multiplier':row['Atr_Multiplier'],
                'SecondarySl': row['SecondarySl'],'TimeBasedExit':None,
                'CPR_CONDITION':False,"target_value":None,"stoploss_value":None,'trighigh':None,'triglow':None,'Trade':None,
                "runtime": datetime.now(),'EntryTime': row['EntryTime'],'ExitTime': row['ExitTime'],'Atr_Period':row['Atr_Period'],
                'StrikeNumber': row['StrikeNumber'],'strikestep': row['strikestep'],'TradeExpiery':row['TradeExpiery'],'USEEXPIERY':row['USEEXPIERY'],

            }
            result_dict[row['Symbol']] = symbol_dict
        print("result_dict: ", result_dict)
    except Exception as e:
        print("Error happened in fetching symbol", str(e))

get_user_settings()
def get_api_credentials():
    credentials = {}

    try:
        df = pd.read_csv('Credentials.csv')
        for index, row in df.iterrows():
            title = row['Title']
            value = row['Value']
            credentials[title] = value
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return credentials

credentials_dict = get_api_credentials()
redirect_uri = credentials_dict.get('redirect_uri')
client_id = credentials_dict.get('client_id')
secret_key = credentials_dict.get('secret_key')
grant_type = credentials_dict.get('grant_type')
response_type = credentials_dict.get('response_type')
state = credentials_dict.get('state')
TOTP_KEY = credentials_dict.get('totpkey')
FY_ID = credentials_dict.get('FY_ID')
PIN = credentials_dict.get('PIN')
# FyresIntegration.apiactivation(client_id=client_id, redirect_uri=redirect_uri, secret_key=secret_key,grant_type=grant_type,response_type=response_type,state=state)

def symbols():
    url = "https://public.fyers.in/sym_details/NSE_FO_sym_master.json"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data, orient='index')
    column_mapping = {
        "lastUpdate": "lastUpdate","exSymbol": "exSymbol","qtyMultiplier": "qtyMultiplier","previousClose": "previousClose",
        "exchange": "exchange","exSeries": "exSeries","optType": "optType","mtf_margin": "mtf_margin","is_mtf_tradable": "is_mtf_tradable",
        "exSymName": "exSymName","symTicker": "symTicker","exInstType": "exInstType","fyToken": "fyToken","upperPrice": "upperPrice",
        "lowerPrice": "lowerPrice","segment": "segment","symbolDesc": "symbolDesc","symDetails": "symDetails","exToken": "exToken",
        "strikePrice": "strikePrice","minLotSize": "minLotSize","underFyTok": "underFyTok","currencyCode": "currencyCode","underSym": "underSym","expiryDate": "expiryDate",
        "tradingSession": "tradingSession","asmGsmVal": "asmGsmVal","faceValue": "faceValue","tickSize": "tickSize","exchangeName": "exchangeName",
        "originalExpDate": "originalExpDate","isin": "isin","tradeStatus": "tradeStatus","qtyFreeze": "qtyFreeze","previousOi": "previousOi",
        "fetchHistory":None,"pphit":None,"Remainingqty":None
    }
    df.rename(columns=column_mapping, inplace=True)
    for col in column_mapping.values():
        if col not in df.columns:
            df[col] = None
    csv_file = 'Master.csv'
    df.to_csv(csv_file, index=False)
    print(f'Fno data has been successfully written to {csv_file}')


FyresIntegration.automated_login(client_id=client_id, redirect_uri=redirect_uri, secret_key=secret_key, FY_ID=FY_ID,
                                     PIN=PIN, TOTP_KEY=TOTP_KEY)

symbols()
def write_to_order_logs(message):
    with open('OrderLog.txt', 'a') as file:  # Open the file in append mode
        file.write(message + '\n')

pivot = None
bc = None
tc = None

def get_max_delta_strike(strikelist):
    max_delta = -float("inf")  # Initialize with negative infinity
    max_delta_strike = None
    for strike, delta in strikelist.items():
        if delta > max_delta:
            max_delta = delta
            max_delta_strike = strike
    return max_delta_strike

def round_to_nearest(number, nearest):
    return round(number / nearest) * nearest
def main_strategy():
    global result_dict,once,pivot,bc,tc

    try:
        for symbol, params in result_dict.items():
            symbol_value = params['Symbol']
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")

            if isinstance(symbol_value, str):
                date_object = datetime.strptime(params['EXPIERY'], '%d-%b-%y')
                new_date_string = date_object.strftime('%y%b').upper()
                formatedsymbol = f"NSE:{params['Symbol']}{new_date_string}FUT"
                if params['Symbol']=="SENSEX":
                    formatedsymbol = f"BSE:{params['Symbol']}{new_date_string}FUT"
                # print(f"{timestamp} Fetching data {formatedsymbol}")

                EntryTime = params['EntryTime']
                EntryTime = datetime.strptime(EntryTime, "%H:%M").time()
                ExitTime = params['ExitTime']
                ExitTime = datetime.strptime(ExitTime, "%H:%M").time()
                current_time = datetime.now().time()
                if current_time>EntryTime and current_time < ExitTime and params['once']==False:
                    params['once']=True
                    YesterdayOhlc=FyresIntegration.fetchOHLC(symbol= formatedsymbol,resolution="1D",atrperiod=params['Atr_Period'])
                    second_last_day = YesterdayOhlc.iloc[-2]
                    second_last_high = second_last_day[2]
                    second_last_low = second_last_day[3]
                    second_last_close = second_last_day[4]
                    pivot = (second_last_high + second_last_low + second_last_close) / 3
                    bc = (second_last_high + second_last_low) / 2
                    tc = (pivot - bc) + pivot
                    # print(f"{formatedsymbol} pivot: ", pivot)
                    # print(f"{formatedsymbol} bc: ", bc)
                    # print(f"{formatedsymbol} tc: ", tc)
                    presentDay=FyresIntegration.fetchOHLC(symbol= formatedsymbol,resolution=params['TimeFrame'],atrperiod=params['Atr_Period'])
                    # print("presentDay: ", presentDay)
                    previousBar = presentDay.iloc[-2]

                    # print("previousBar: ", previousBar)
                    previousBar_high = previousBar[2]
                    previousBar_low = previousBar[3]
                    params['trighigh']=previousBar_high
                    params['triglow']=previousBar_low

                if current_time>EntryTime and current_time < ExitTime and datetime.now() >= params["runtime"]:
                    try:
                        time.sleep(int(1))
                        presentDay = FyresIntegration.fetchOHLC(symbol=formatedsymbol, resolution=params['TimeFrame'],atrperiod=params['Atr_Period'])
                        previousBar = presentDay.iloc[-1]
                        currentBar = presentDay.iloc[-1]
                        currentBar_close = currentBar[4]
                        # print("previousBar: ",previousBar)
                        previousBar_close=previousBar[4]
                        previousBar_low = previousBar[3]
                        previousBar_high = previousBar[2]
                        if params['Trade']=="BUY":
                            atr = previousBar[6]
                            params["SecondarySl"] = previousBar_low-(atr*float(params['Atr_Multiplier']))
                        if params['Trade']=="SHORT":
                            atr = previousBar[6]
                            params["SecondarySl"] = previousBar_high + (atr*float(params['Atr_Multiplier']))
                        next_specific_part_time = datetime.now() + timedelta(
                                seconds=determine_min(params["TimeFrame"]) * 60)
                        next_specific_part_time = round_down_to_interval(next_specific_part_time,
                                                                             determine_min(str(params["TimeFrame"])))
                        print("Next datafetch time = ", next_specific_part_time)
                        params['runtime'] = next_specific_part_time
                    except Exception as e:
                        print("Error happened in fetching data : ", str(e))
                        traceback.print_exc()



                if current_time>EntryTime and current_time < ExitTime and params['USE_CPR']==True:
                    if previousBar_close>bc:
                        params['CPR_CONDITION']="BUY"
                    if previousBar_close<tc:
                        params['CPR_CONDITION']="SHORT"
                if params['USE_CPR']==False:
                    params['CPR_CONDITION']="BOTH"

                if current_time > EntryTime and current_time < ExitTime:
                    print(f"{timestamp} {formatedsymbol} previousBar_close:{previousBar_close},pivot: {pivot}"
                          f" bc: {bc}, tc: {tc},Trade: {params['Trade']},stoploss_value: {params['stoploss_value']}"
                          f",parttial qty: {params['PartialProfitQty']},SecondarySl: {params['SecondarySl']}")



                if current_time>EntryTime and current_time < ExitTime and  previousBar_close>params['trighigh'] and (params['CPR_CONDITION']=="BUY" or params['CPR_CONDITION']=="BOTH"):
                    params["stoploss_value"]=previousBar_low
                    params['Trade']="BUY"
                    params["pphit"]= "NOHIT"
                    params["Remainingqty"]= params[ 'Quantity']-params['PartialProfitQty']
                    params['TimeBasedExit']= "TAKEEXIT"
                    strikelist = getstrikes_call(ltp=round_to_nearest(number=currentBar_close, nearest=params['strikestep']),
                                                 step=params['StrikeNumber'],
                                                 strikestep=params['strikestep'])
                    for strike in strikelist:
                        delta = float(
                            option_delta_calculation(symbol=symbol, expiery=params['TradeExpiery'], strike=strike,
                                                     optiontype="CE",
                                                     underlyingprice=currentBar_close, MODE=params["USEEXPIERY"]))
                        strikelist[strike] = delta
                    final = get_max_delta_strike(strikelist)
                    optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{final}CE"
                    if symbol == "SENSEX":
                        optionsymbol = f"BSE:{symbol}{params['TradeExpiery']}{final}CE"
                    OrderLog=(f"{timestamp} Buy order executed @ {formatedsymbol}, "
                              f"stoploss={params['stoploss_value']}, partialqty={params['PartialProfitQty']},order symbol={optionsymbol}")
                    print(OrderLog)
                    write_to_order_logs(OrderLog)


                if current_time>EntryTime and current_time < ExitTime and previousBar_close<params['triglow'] and (params['CPR_CONDITION']=="SHORT" or params['CPR_CONDITION']=="BOTH"):

                    params["stoploss_value"]=previousBar_high
                    params['Trade'] = "SHORT"
                    params["pphit"] = "NOHIT"
                    params["Remainingqty"] = params['Quantity'] - params['PartialProfitQty']
                    params['TimeBasedExit'] = "TAKEEXIT"
                    strikelist = getstrikes_put(
                        ltp=round_to_nearest(number=currentBar_close, nearest=params['strikestep']),
                        step=params['StrikeNumber'],
                        strikestep=params['strikestep'])
                    for strike in strikelist:
                        delta = float(
                            option_delta_calculation(symbol=symbol, expiery=params['TradeExpiery'], strike=strike,
                                                     optiontype="CE",
                                                     underlyingprice=currentBar_close, MODE=params["USEEXPIERY"]))
                        strikelist[strike] = delta
                    final = get_max_delta_strike(strikelist)
                    optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{final}CE"
                    if symbol == "SENSEX":
                        optionsymbol = f"BSE:{symbol}{params['TradeExpiery']}{final}CE"
                    OrderLog = (f"{timestamp} Sell order executed @ {formatedsymbol}, "
                                f"stoploss={params['stoploss_value']}, partialqty={params['PartialProfitQty']}, order symbol: {optionsymbol}")
                    print(OrderLog)
                    write_to_order_logs(OrderLog)


                if params['Trade']=="BUY" and params['Trade'] is not None :
                    if params["stoploss_value"] is not None and currentBar_close<=params["stoploss_value"]:
                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp} Stoploss  booked buy trade @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                        if params["pphit"] == "HIT":
                            OrderLog = f"{timestamp} Stoploss  booked buy trade @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"

                    if current_time == ExitTime and params['TimeBasedExit'] == "TAKEEXIT" and (params["pphit"]=="HIT" or params["pphit"]=="NOHIT" ) :
                        if params["pphit"]=="HIT":
                            OrderLog = f"{timestamp} Time Based exit happened @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit']= "NOMORETRADES"

                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp}  Time Based exit happened @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit'] = "NOMORETRADES"

                    if params["SecondarySl"] is not None and currentBar_close<=params["SecondarySl"] and params["pphit"] == "NOHIT":
                        params["pphit"] = "HIT"
                        OrderLog = f"{timestamp} Partial Stoploss  booked buy trade @ {formatedsymbol} @ {currentBar_close}, lotsize={params['PartialProfitQty']}"
                        print(OrderLog)
                        write_to_order_logs(OrderLog)

                if params['Trade']=="SHORT" and params['Trade'] is not None :

                    if params["stoploss_value"] is not None and currentBar_close >= params["stoploss_value"]:
                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp} Stoploss  booked sell trade @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"]="NOMORETRADES"

                        if params["pphit"] == "HIT":
                            OrderLog = f"{timestamp} Stoploss  booked sell trade @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"

                    if current_time == ExitTime and params['TimeBasedExit'] == "TAKEEXIT" and (params["pphit"]=="HIT" or params["pphit"]=="NOHIT" ) :
                        if params["pphit"]=="HIT":
                            OrderLog = f"{timestamp} Time Based exit happened @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit'] = "NOMORETRADES"

                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp}  Time Based exit happened @ {formatedsymbol} @ {currentBar_close}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit'] = "NOMORETRADES"

                    if params["SecondarySl"] is not None and currentBar_close >= params["SecondarySl"] and params["pphit"] == "NOHIT":
                        params["pphit"] = "HIT"
                        OrderLog = f"{timestamp} Partial Stoploss sell trade @ {formatedsymbol} @ {currentBar_close}, lotsize={params['PartialProfitQty']}"
                        print(OrderLog)
                        write_to_order_logs(OrderLog)

    except Exception as e:
        print("Error in main strategy : ", str(e))
        traceback.print_exc()


while True:
    main_strategy()
    time.sleep(2)