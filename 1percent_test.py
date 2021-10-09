import time
import pyupbit
import datetime
import pandas as pd
import telegram
import talib

TOKEN = '1919980133:AAG845Pwz1i4WCJvaaamRT-_QE0uezlvA9A'
ID = '1796318367'
#단체방
ID2 = '-548871861'
bot = telegram.Bot(TOKEN)


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minutes60", count=1)
    start_time = df.index[0]
    return start_time

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_volatility(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    df['volatility'] = (df['close']/df['open']-1)*100
    volatility = df.iloc[-1]['volatility']
    return volatility

def get_minute(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute1", count=2)
    df['volatility'] = (df['close']/df['open']-1)*100
    volatility = df.iloc[-1]['volatility']
    return volatility

def check_vol(ticker):
    df_d = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    df_m = pyupbit.get_ohlcv(ticker, interval="minute1", count=2)
    pre=(df_m.iloc[0]['close']/df_d['close'][0]-1)*100
    post=(df_m.iloc[-1]['close']/df_d['close'][0]-1)*100
    result=[pre,post]
    return result

def check_profit(ticker,price,total):
    buy_value = price * total
    current_price = get_current_price(ticker)
    current_value = current_price * total
    profit = round(((current_value/buy_value)-1)*100,2)
    return profit

def get_top5(rq):
    tickers = pyupbit.get_tickers(fiat="KRW")
    dfs = []
    for i in range(len(tickers)):
        volatility = round(get_volatility(tickers[i]),2)
        dfs.append(volatility)
        time.sleep(0.1)

    volatility = pd.DataFrame({"volatility": dfs})
    ticker = pd.DataFrame({"ticker": pyupbit.get_tickers(fiat="KRW")})
    sum = [ticker, volatility]
    all_volatility = pd.concat(sum, axis =1)
    final=all_volatility.sort_values(by = "volatility", ascending=False)
    if rq == 0:
        #Dataframe을 list로 변환
        #result = final.iloc[:5]
        result = final.iloc[0]['ticker'].values.tolist()
    elif rq ==1:
        #상위 상승률 top5 ticker명만 뽑기
        result = final.iloc[:5]['ticker'].values.tolist()
    else:
        #상위 상승률 top5 상승률만 뽑기
        result2 = final.iloc[:5]['volatility'].values.tolist()
    return result[0]

def get_cci(ticker):
    period = 14
    df = pyupbit.get_ohlcv(ticker, interval = 'minute1', count = 200)
    df["CCI"] = talib.CCI(df["high"], df["low"], df["close"], period)
    cci = df['CCI'][-2]
    return cci

def get_rsi(ticker):
    period = 14
    df = pyupbit.get_ohlcv(ticker, interval = 'minute1', count = 200)
    df["RSI"] = talib.RSI(df["close"], period)
    rsi = df['RSI'][-2]
    return rsi

bot.sendMessage(ID, "start")

ticker_check = False
check_buy = False
check_trade = False
check_inform = False
check_success = False
my_money = 1000000

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-ETH")
        end_time = start_time + datetime.timedelta(hours=1)
        if start_time < now < end_time - datetime.timedelta(seconds=5):
            check_inform = False
            if ticker_check == False:
                print("ticker check")
                get_ticker = get_top5(1)
                check_time = datetime.datetime.now()
                bot.sendMessage(ID2, str(check_time) + '\n'
                                + "ticker: " + str(get_ticker))
                ticker_check = True
            cci = get_cci(get_ticker)
            rsi = get_rsi(get_ticker)
            if cci < (-100) and rsi < 30 and check_buy == False and check_trade == False:
                print('매수 하러 옴')
                current_price = get_current_price(get_ticker)
                buy_time = datetime.datetime.now()
                buy_date = now.strftime('%b/%d')
                buy_ticker = get_ticker
                buy_price =  current_price 
                buy_total =(my_money*0.9995*0.996)/buy_price
                bot.sendMessage(ID2, str(buy_ticker) + '\n'
                                + "buy_time:" + str(buy_time) + '\n'
                                + "buy price:" + str(buy_price) + '\n'
                                + "buy total:" + str(buy_total) + '\n'
                                + "test...ing")
                my_money = 0
                check_buy = True
            if check_buy == True and check_trade == False:
                print("수익 확인중")
                current_profit = check_profit(buy_ticker,buy_price,buy_total)
                if current_profit >= 1.5:
                    print('수익실현 하러 옴')
                    sell_price = get_current_price(buy_ticker)
                    sell_time = datetime.datetime.now()
                    my_money = sell_price*(buy_total*0.9995*0.996)
                    bot.sendMessage(ID2, str(buy_ticker) + '\n'
                                    + "sell_time:" + str(sell_time) + '\n'
                                    + "sell price:" + str(sell_price) + '\n'
                                    + "my_money:" + str(my_money) + '\n'
                                    + "1percent success" + '\n'
                                    + "test...ing")
                    check_trade = True
                    check_buy = False
                    check_success = True   
        else:
            if check_inform == False:
                print('리셋하러 옴')
                #매수/매도, 익절
                if check_trade == True and check_success == True:
                    bot.sendMessage(ID2, 'win..rest...' + '\n'
                                        + 'my_money: ' + str(my_money))
                #매수, 전량매도
                elif check_buy == True and check_trade == False:
                    remove_price = get_current_price(buy_ticker)
                    remove_profit = check_profit(buy_ticker,buy_price,buy_total)
                    my_money = remove_price*(buy_total*0.9995*0.996)
                    bot.sendMessage(ID2, 'sell...everything..' + '\n'
                                    + "profit:" + str(remove_profit) + '\n'
                                    + "sell price:" + str(remove_price) + '\n'
                                    + "my_money:" + str(my_money) + '\n'
                                    + "test...ing")
                #매수 못함/매도 몸함,
                elif check_trade == False and check_buy == False:
                    bot.sendMessage(ID2, 'draw..rest...' + '\n'
                                        + 'my_money: ' + str(my_money))
                else:
                    bot.sendMessage(ID2, str(check_trade) + '\n'
                                        + str(check_buy) + '\n'
                                        + str(check_success))
                check_inform = True
            check_trade = False
            check_buy = False
            check_success = False
            ticker_check = False
            print('변수 초기화 완료')
        time.sleep(1)
    except Exception as e:
        print(e)
        bot.sendMessage(ID, e)
        time.sleep(1)
