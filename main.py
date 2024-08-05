import threading
import requests
import AngelIntegration,AliceBlueIntegration
import time
import traceback
from datetime import datetime, timedelta
import pandas as pd
result_dict={}
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta

AliceBlueIntegration.load_alice()
AliceBlueIntegration.get_nfo_instruments()

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
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    short_format = date_obj.strftime("%y%b").upper()  # Convert to uppercase
    return short_format

def convert_julian_date(date_object):
    year = date_object.year
    month = date_object.month
    day = date_object.day
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn


def get_delta(strikeltp,underlyingprice,strike,timeexpiery,riskfreeinterest,flag):
    # flag me  call  'c' ya put 'p'
    from py_vollib.black_scholes.greeks.analytical import delta
    iv= implied_volatility(price=strikeltp,S=underlyingprice,K=strike,t=timeexpiery,r=riskfreeinterest,flag=flag)
    value = delta(flag,underlyingprice,strike,timeexpiery,riskfreeinterest,iv)
    print("delta",value)
    return value


def option_delta_calculation(symbol,expiery,Tradeexp,strike,optiontype,underlyingprice,MODE):
    date_obj = datetime.strptime(Tradeexp, "%d-%b-%y")
    formatted_date = date_obj.strftime("%d%b%y").upper()
    optionsymbol = f"{symbol}{formatted_date}{strike}{optiontype}"
    # print("optionsymbol option delta: ",optionsymbol)
    optionltp=AngelIntegration.get_ltp(segment="NFO", symbol=optionsymbol,
                             token=get_token(optionsymbol))
    # print("optionltp option delta: ", optionltp)
    # print("Main expiery: ", expiery)
    if MODE == "WEEKLY":
        date_object = datetime.strptime(expiery, '%d-%b-%y')
        distanceexp = convert_julian_date(date_object)
        print("WEEKLY: ",distanceexp)
    if MODE == "MONTHLY":
        distanceexp = datetime.strptime(expiery, "%d-%b-%y")  # Convert string to datetime object if necessary
        print("MONTHLY: ",distanceexp)
    # print("distanceexp: ", distanceexp)
    # print("distanceexp: ",distanceexp)
    t= (distanceexp-datetime.now())/timedelta(days=1)/365
    print("t: ",t)
    if optiontype=="CE":
        fg="c"
    else :
        fg = "p"
    # print("optionltp: ",optionltp)
    # print("underlyingprice: ", underlyingprice)
    # print("strike: ", strike)
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
                'SecondarySl':None,'TimeBasedExit':None,'callstrike':None,'putstrike':None,"producttype": row['PRODUCT_TYPE'],
                'CPR_CONDITION':False,"target_value":None,"stoploss_value":None,'trighigh':None,'triglow':None,'Trade':None,
                "runtime": datetime.now(),'EntryTime': row['EntryTime'],'ExitTime': row['ExitTime'],'Atr_Period':row['Atr_Period'],
                'StrikeNumber': row['StrikeNumber'],'strikestep': row['strikestep'],'TradeExpiery':row['TradeExpiery'],'USEEXPIERY':row['USEEXPIERY'],
                'exch':None,'aliceexp':None,'AliceblueTradeExp': row['AliceblueTradeExp'],'TF_INT':row['TF_INT'],"BASESYMBOL":row['BASESYMBOL'],
                'previousBar_close':None,'currentBar_close':None

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
stockdevaccount=credentials_dict.get('stockdevaccount')
api_key=credentials_dict.get('apikey')
username=credentials_dict.get('USERNAME')
pwd=credentials_dict.get('pin')
totp_string=credentials_dict.get('totp_string')
AngelIntegration.login(api_key=api_key,username=username,pwd=pwd,totp_string=totp_string)

# AngelIntegration.symbolmpping() unblock later


def get_token(symbol):
    df= pd.read_csv("Instrument.csv")
    row = df.loc[df['symbol'] == symbol]
    if not row.empty:
        token = row.iloc[0]['token']
        return token


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

currentBar_close = 0
previousBar_close=0
previousBar_low = 0
previousBar_high =0

def main_strategy():
    global result_dict,once,pivot,bc,tc,previousBar_close,currentBar_close,previousBar_low,previousBar_high
    print("main_strategy running ")
    try:
        for symbol, params in result_dict.items():
            symbol_value = params['Symbol']
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")

            if isinstance(symbol_value, str):
                date_object = datetime.strptime(params['EXPIERY'], '%d-%b-%y')
                new_date_string = date_object.strftime('%y%b').upper()
                segment="NSE"
                EntryTime = params['EntryTime']
                EntryTime = datetime.strptime(EntryTime, "%H:%M").time()
                ExitTime = params['ExitTime']
                ExitTime = datetime.strptime(ExitTime, "%H:%M").time()
                current_time = datetime.now().time()
                print("symbol_value: ",symbol_value)
                if current_time>EntryTime and current_time < ExitTime and params['once']==False:
                    params['once']=True
                    print(f"get_token{params['Symbol']}: ",get_token(params['Symbol']))
                    YesterdayOhlc=AngelIntegration.get_historical_data(symbol=params['Symbol'], token=get_token(params['Symbol']), timeframe='ONE_DAY', segment=segment)
                    # print("YesterdayOhlc: ", YesterdayOhlc)
                    second_last_day = YesterdayOhlc.iloc[-2]
                    # print("second_last_day: ", second_last_day)
                    second_last_high = second_last_day[2]
                    # print("second_last_high: ", second_last_high)
                    second_last_low = second_last_day[3]
                    # print("second_last_low: ", second_last_low)
                    second_last_close = second_last_day[4]
                    # print("second_last_close: ", second_last_close)
                    pivot = (second_last_high + second_last_low + second_last_close) / 3
                    bc = (second_last_high + second_last_low) / 2
                    tc = (pivot - bc) + pivot

                    presentDay=AngelIntegration.get_historical_data_atr(symbol= params['Symbol'], token=get_token(params['Symbol']),
                                                                        timeframe=params['TimeFrame'],atr=params['Atr_Period'], segment=segment)
                    # print("presentDay: ", presentDay)
                    previousBar = presentDay.iloc[-2]
                    # print("previousBar: ", previousBar)
                    previousBar_high = previousBar[2]
                    previousBar_low = previousBar[3]
                    # print("previousBar_high: ", previousBar_high)
                    # print("previousBar_low: ", previousBar_low)
                    params['trighigh']=previousBar_high
                    params['triglow']=previousBar_low

                if current_time>EntryTime and current_time < ExitTime and datetime.now() >= params["runtime"]:
                    try:
                        time.sleep(int(1))
                        presentDay = AngelIntegration.get_historical_data_atr(symbol= params['Symbol'], token=get_token(params['Symbol']),
                                                                        timeframe=params['TimeFrame'],atr=params['Atr_Period'], segment=segment)
                        previousBar = presentDay.iloc[-2]
                        print("previousBar: ",previousBar)
                        currentBar = presentDay.iloc[-1]
                        currentBar_close = currentBar[4]
                        previousBar_close=previousBar[4]
                        previousBar_low = previousBar[3]
                        previousBar_high = previousBar[2]
                        params['previousBar_close']= previousBar_close
                        params['currentBar_close']= currentBar_close
                        if params['Trade']=="BUY":
                            atr = previousBar[6]
                            params["SecondarySl"] = previousBar_low-(atr*float(params['Atr_Multiplier']))
                        if params['Trade']=="SHORT":
                            atr = previousBar[6]
                            params["SecondarySl"] = previousBar_high + (atr*float(params['Atr_Multiplier']))
                        next_specific_part_time = datetime.now() + timedelta(
                                seconds=determine_min(str(params["TF_INT"])) * 60)
                        next_specific_part_time = round_down_to_interval(next_specific_part_time,
                                                                             determine_min(str(params["TF_INT"])))
                        print("Next datafetch time = ", next_specific_part_time)
                        params['runtime'] = next_specific_part_time
                    except Exception as e:
                        print("Error happened in fetching data : ", str(e))
                        traceback.print_exc()



                if current_time>EntryTime and current_time < ExitTime and params['USE_CPR']==True:
                    if params['previousBar_close']>bc:
                        params['CPR_CONDITION']="BUY"
                    if params['previousBar_close']<tc:
                        params['CPR_CONDITION']="SHORT"
                if params['USE_CPR']==False:
                    params['CPR_CONDITION']="BOTH"

                if current_time > EntryTime and current_time < ExitTime:
                    print(f"{timestamp} {params['Symbol']} previousBar_close:{params['previousBar_close']},pivot: {pivot}"
                          f" bc: {bc}, tc: {tc},Trade: {params['Trade']},stoploss_value: {params['stoploss_value']}"
                          f",parttial qty: {params['PartialProfitQty']},SecondarySl: {params['SecondarySl']}")
                    # strikelist = getstrikes_call(
                    #     ltp=round_to_nearest(number=params['currentBar_close'], nearest=params['strikestep']),
                    #     step=params['StrikeNumber'],
                    #     strikestep=params['strikestep'])
                    # print("Collection:", strikelist)
                    # for strike in strikelist:
                    #     date_format = '%d-%b-%y'
                    #
                    #     delta = float(
                    #         option_delta_calculation(symbol=params['BASESYMBOL'], expiery=str(params['TradeExpiery']),
                    #                                  Tradeexp=params['TradeExpiery'],
                    #                                  strike=strike,
                    #                                  optiontype="CE",
                    #                                  underlyingprice=params['currentBar_close'], MODE=params["USEEXPIERY"]))
                    #     strikelist[strike] = delta
                    #
                    # print("strikelist: ", strikelist)
                    # final = get_max_delta_strike(strikelist)
                    # print("Final strike: ", final)
                    # params['exch']="NFO"
                    # aliceexp = datetime.strptime(params['AliceblueTradeExp'], '%d-%b-%y')
                    # aliceexp = aliceexp.strftime('%Y-%m-%d')
                    # params['aliceexp'] = aliceexp



                if (current_time>EntryTime and current_time < ExitTime and  params['previousBar_close']>params['trighigh']
                        and (params['CPR_CONDITION']=="BUY" or params['CPR_CONDITION']=="BOTH")):
                    params["stoploss_value"]=previousBar_low
                    params['Trade']="BUY"
                    params["pphit"]= "NOHIT"
                    params["Remainingqty"]= params[ 'Quantity']-params['PartialProfitQty']
                    params['TimeBasedExit']= "TAKEEXIT"
                    strikelist = getstrikes_call(
                        ltp=round_to_nearest(number=params['currentBar_close'], nearest=params['strikestep']),
                        step=params['StrikeNumber'],
                        strikestep=params['strikestep'])
                    print("Collection:", strikelist)
                    for strike in strikelist:
                        date_format = '%d-%b-%y'

                        delta = float(
                            option_delta_calculation(symbol=params['BASESYMBOL'], expiery=str(params['TradeExpiery']),
                                                     Tradeexp=params['TradeExpiery'],
                                                     strike=strike,
                                                     optiontype="CE",
                                                     underlyingprice=params['currentBar_close'], MODE=params["USEEXPIERY"]))
                        strikelist[strike] = delta

                    print("strikelist: ", strikelist)
                    final = get_max_delta_strike(strikelist)
                    print("Final strike: ", final)
                    params['callstrike'] = final

                    optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{final}CE"
                    params['exch'] = "NFO"

                    aliceexp = datetime.strptime(params['AliceblueTradeExp'], '%d-%b-%y')
                    aliceexp = aliceexp.strftime('%Y-%m-%d')
                    params['aliceexp'] = aliceexp
                    print("exch: ", params['exch'])
                    print("symbol: ", symbol)

                    AliceBlueIntegration.buy(quantity=int(params["Quantity"]), exch=params['exch'], symbol=params['BASESYMBOL'],
                                             expiry_date=params['aliceexp'],
                                             strike=params['callstrike'], call=True, producttype=params["producttype"])

                    OrderLog = (f"{timestamp} Buy order executed @ {params['Symbol']}, "
                                f"stoploss={params['stoploss_value']}, partialqty={params['PartialProfitQty']},order symbol={optionsymbol}")
                    print(OrderLog)
                    write_to_order_logs(OrderLog)



                if (current_time>EntryTime and current_time < ExitTime and params['previousBar_close']<params['triglow']
                        and (params['CPR_CONDITION']=="SHORT" or params['CPR_CONDITION']=="BOTH")):
                    params["stoploss_value"]=previousBar_high
                    params['Trade'] = "SHORT"
                    params["pphit"] = "NOHIT"
                    params["Remainingqty"] = params['Quantity'] - params['PartialProfitQty']
                    params['TimeBasedExit'] = "TAKEEXIT"
                    strikelist = getstrikes_call(
                        ltp=round_to_nearest(number=params['currentBar_close'], nearest=params['strikestep']),
                        step=params['StrikeNumber'],
                        strikestep=params['strikestep'])
                    print("Collection:", strikelist)
                    for strike in strikelist:
                        date_format = '%d-%b-%y'

                        delta = float(
                            option_delta_calculation(symbol=params['BASESYMBOL'], expiery=str(params['TradeExpiery']),
                                                     Tradeexp=params['TradeExpiery'],
                                                     strike=strike,
                                                     optiontype="PE",
                                                     underlyingprice=params['currentBar_close'],
                                                     MODE=params["USEEXPIERY"]))
                        strikelist[strike] = delta

                    print("strikelist: ", strikelist)
                    final = get_max_delta_strike(strikelist)
                    print("Final strike: ", final)
                    params['callstrike'] = final
                    optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{final}PE"
                    params['exch'] = "NFO"

                    aliceexp = datetime.strptime(params['AliceblueTradeExp'], '%d-%b-%y')
                    aliceexp = aliceexp.strftime('%Y-%m-%d')
                    params['aliceexp'] = aliceexp
                    print("exch: ", params['exch'])
                    print("symbol: ", symbol)

                    AliceBlueIntegration.buy(quantity=int(params["Quantity"]), exch=params['exch'], symbol=params['BASESYMBOL'],
                                             expiry_date=params['aliceexp'],
                                             strike=params['putstrike'], call=False, producttype=params["producttype"])

                    OrderLog = (f"{timestamp} Sell order executed @ {symbol}, "
                                f"stoploss={params['stoploss_value']}, partialqty={params['PartialProfitQty']}, order symbol: {optionsymbol}")
                    print(OrderLog)
                    write_to_order_logs(OrderLog)


                if params['Trade']=="BUY" and params['Trade'] is not None :
                    if params["stoploss_value"] is not None and params['currentBar_close']<=params["stoploss_value"]:
                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp} Stoploss  booked buy trade @ {symbol} @ {params['currentBar_close']}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"

                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["callstrike"], call=True,
                                                         producttype=params["producttype"])
                        if params["pphit"] == "HIT":
                            OrderLog = f"{timestamp} Stoploss  booked buy trade @ {symbol} @ {params['currentBar_close']}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            AliceBlueIntegration.buyexit(quantity=params["Remainingqty"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["callstrike"], call=True,
                                                         producttype=params["producttype"])

                    if current_time == ExitTime and params['TimeBasedExit'] == "TAKEEXIT" and (params["pphit"]=="HIT" or params["pphit"]=="NOHIT" ) :
                        if params["pphit"]=="HIT":
                            OrderLog = f"{timestamp} Time Based exit happened @ {symbol} @ {params['currentBar_close']}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit']= "NOMORETRADES"
                            AliceBlueIntegration.buyexit(quantity=params["Remainingqty"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["callstrike"], call=True,
                                                         producttype=params["producttype"])

                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp}  Time Based exit happened @ {symbol} @ {params['currentBar_close']}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit'] = "NOMORETRADES"
                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'], symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["callstrike"], call=True,
                                                         producttype=params["producttype"])

                    if params["SecondarySl"] is not None and params['currentBar_close']<=params["SecondarySl"] and params["pphit"] == "NOHIT":
                        params["pphit"] = "HIT"
                        AliceBlueIntegration.buyexit(quantity=params["PartialProfitQty"], exch=params['exch'], symbol=params['BASESYMBOL'],
                                                     expiry_date=params['aliceexp'],
                                                     strike=params["callstrike"], call=True,
                                                     producttype=params["producttype"])
                        OrderLog = f"{timestamp} Partial Stoploss  booked buy trade @ {symbol} @ {params['currentBar_close']}, lotsize={params['PartialProfitQty']}"
                        print(OrderLog)
                        write_to_order_logs(OrderLog)

                if params['Trade']=="SHORT" and params['Trade'] is not None :

                    if params["stoploss_value"] is not None and params['currentBar_close'] >= params["stoploss_value"]:
                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp} Stoploss  booked sell trade @ {symbol} @ {params['currentBar_close']}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"]="NOMORETRADES"
                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["putstrike"], call=False,
                                                         producttype=params["producttype"])

                        if params["pphit"] == "HIT":
                            OrderLog = f"{timestamp} Stoploss  booked sell trade @ {symbol} @ {params['currentBar_close']}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            AliceBlueIntegration.buyexit(quantity=params["Remainingqty"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["putstrike"], call=False,
                                                         producttype=params["producttype"])


                    if current_time == ExitTime and params['TimeBasedExit'] == "TAKEEXIT" and (params["pphit"]=="HIT" or params["pphit"]=="NOHIT" ) :
                        if params["pphit"]=="HIT":
                            OrderLog = f"{timestamp} Time Based exit happened @ {symbol} @ {params['currentBar_close']}, lotsize={params['Remainingqty']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit'] = "NOMORETRADES"
                            AliceBlueIntegration.buyexit(quantity=params["Remainingqty"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["putstrike"], call=False,
                                                         producttype=params["producttype"])

                        if params["pphit"] == "NOHIT":
                            OrderLog = f"{timestamp}  Time Based exit happened @ {symbol} @ {params['currentBar_close']}, lotsize={params['Quantity']}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            params["pphit"] = "NOMORETRADES"
                            params['TimeBasedExit'] = "NOMORETRADES"
                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["putstrike"], call=False,
                                                         producttype=params["producttype"])

                    if params["SecondarySl"] is not None and params['currentBar_close'] >= params["SecondarySl"] and params["pphit"] == "NOHIT":
                        params["pphit"] = "HIT"
                        AliceBlueIntegration.buyexit(quantity=params["PartialProfitQty"], exch=params['exch'], symbol=params['BASESYMBOL'],
                                                     expiry_date=params['aliceexp'],
                                                     strike=params["putstrike"], call=False,
                                                     producttype=params["producttype"])
                        OrderLog = f"{timestamp} Partial Stoploss sell trade @ {symbol} @ {params['currentBar_close']}, lotsize={params['PartialProfitQty']}"
                        print(OrderLog)
                        write_to_order_logs(OrderLog)

    except Exception as e:
        print("Error in main strategy : ", str(e))
        traceback.print_exc()




while True:
    print("while loop running ")
    main_strategy()
    time.sleep(2)