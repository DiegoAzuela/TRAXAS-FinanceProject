# Libraries
# Libraries needed to do matrix manipulation and calculus
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# Libraries needed to import macro and bursatil data with Quandl and other API´s
import quandl
quandl.ApiConfig.api_key = "v4-zTHgQMzixFvJzHB98"
import pandas_datareader as dr
import pandas_datareader.data as web

# Libraries needed for the financial statements
import simfin as sf
from simfin.names import *
sf.set_api_key("free")
sf.set_data_dir('~/simfin_data/')

#CUIDADO
# Timeseries of US Stock description - Check solution for Local CSV (Name, Symbol, Industry)
#industry = pd.read_csv(r'C:/Users/Alex/Desktop/GitHub/Main-project/Industry_US.csv').reset_index(drop=True)
#NYSE_sym = industry[["Company Name", "SYMBOL", "Industry Group"]].reset_index(drop=True)
#NYSE_sym.dropna(subset=["SYMBOL"], inplace=True)

#Dataframe with description of all possible commands/arguments per function
commands = pd.DataFrame({ "fin_st" : ["income","balance","cash_flow", "Nan", "Nan", "Nan"], "macro_data" : ["Real_GDP", "Unemployment", "Population", "Public_Debt", "US_Bonds", "Sector_performance"], "yahoo_finance" : ["SPY", "DIA", "Other Yfinance command", "Nan","Nan","Nan"]})

#___________________________________________________________________________________________
# Import of esential data (in DataFrame format)

#Functions for data recollection
#Financial Statements

def fin_st(symbol, statement, int='annual'):
    if (statement == "income"):
        fs_equity = sf.load_income(variant=int, market='us')
    elif (statement == "balance"):
        fs_equity = sf.load_balance(variant=int, market='us')
    elif (statement == "cash_flow"):
        fs_equity = sf.load_cashflow(variant=int, market='us')
    elif (statement == "daly_price"):
        fs_equity = sf.load_shareprices(variant=int, market='us')
    return fs_equity.loc[symbol]

#Macroeconomic data

def macro_data(macro):

    macro_commands = pd.DataFrame([["Real_GDP", "FRED/GDPC1"], ["Unemployment", "FRED/UNEMPLOY"], ["Population", "FRED/B230RC0Q173SBEA"],
         ["Public_Debt", "FRED/GFDEGDQ188S"], ["US_Bonds", "USTREASURY/REALYIELD"]],
        columns=["Variable", "Quandl Code"])

    if (macro == "Sector_performance"):
        macro_df = web.get_sector_performance_av(api_key="QRXX1F6QW90T9SOX")
    else:
        quandl_r = macro_commands[macro_commands["Variable"] == macro]
        for variable in quandl_r["Quandl Code"]:
            quandl_code = variable
        macro_df = quandl.get(quandl_code).reset_index()

    return macro_df

#Security and Equity Trading data

def yahoo_finance(symbol, date = "01-01-1970", int = "d"):
    yahoo_v = dr.get_data_yahoo(symbol, start = date, interval = int)
    yahoo_df = pd.DataFrame(yahoo_v).reset_index()
    return yahoo_df

#_____________________________________________________________________________
# Plotting function to check data retrieved

def plot(data_x, data_y, title, label_x, label_y):
    plt.plot(data_x, data_y, color = "blue", linestyle = ":")
    plt.title(title)
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.show()

#__________________________________________________________________________________________________________________
#Data processing and required calculations
#Functions

#Calculating equity beta w.r.t. 5 years of monthly returns
def beta_equity(symbol):
    five_ys = 365.24*5
    five_yago = datetime.today() - timedelta(days=five_ys)
    d = five_yago.strftime('%Y-%m-01')
    equity_df = yahoo_finance(symbol, d, int = "m")
    equity_ndw_i = equity_df[["Date", "Close"]]
    index_df = yahoo_finance("SPY", d, int = "m")
    index_ndw_i = index_df[["Date", "Close"]]
    index_ndw = index_ndw_i.reset_index(drop= True)
    equity_ndw = equity_ndw_i.reset_index(drop= True)
    #Create dataframe with monthly data frequency
    #Subfunction to create return vectors
    equity_ndw["Close - 1"] = equity_ndw["Close"].shift(1)
    equity_ndw["Monthly r (%)"] = (equity_ndw["Close"] - equity_ndw["Close - 1"])*100/(equity_ndw["Close - 1"])
    index_ndw["Close - 1"] = index_ndw["Close"].shift(1)
    index_ndw["Monthly r (%)"] = (index_ndw["Close"] - index_ndw["Close - 1"]) * 100 / (index_ndw["Close - 1"])
    #Analyzing statistics of return vectors
    var_index = index_ndw["Monthly r (%)"].var()
    std_index = index_ndw["Monthly r (%)"].std()
    var_equity = equity_ndw["Monthly r (%)"].var()
    std_equity = equity_ndw["Monthly r (%)"].std()
    mean_equity = equity_ndw["Monthly r (%)"].mean()
    mean_index = index_ndw["Monthly r (%)"].mean()
    #Get correlation between index and equity
    return_df = pd.concat([index_ndw[["Date","Monthly r (%)"]], equity_ndw["Monthly r (%)"]], axis=1, join='inner')
    return_df.columns  = ["Date", "Index Monthly r", "Stock Monthly r"]
    cov_df = return_df.cov()
    cov_factor = cov_df.iloc[1]["Index Monthly r"]
    ##corr_returns = return_df.corr()
    ##corr_factor = corr_returns.iloc[1]["Index Daily r"]
    #Last calculation to get Be
    ##beta = (corr_factor)*(std_equity)/(std_index)
    beta = cov_factor/var_index
    return beta

#Important Ratios

def Current_Ratio(symbol, int='quarterly'):
        Df = fin_st(symbol, 'balance', int)
        CR = Df[['Total Current Assets', 'Total Current Liabilities']]
        CRN = CR.rename(columns={'Total Current Assets': 'TCA', 'Total Current Liabilities': 'TCL'})
        CRN['Current Ratio'] = CRN['TCA'] / CRN['TCL']
        return CRN['Current Ratio']

def Cash_Ratio(symbol, int='quarterly'):
        Df = fin_st(symbol, 'balance', int)
        CR = Df[['Total Current Liabilities', 'Cash, Cash Equivalents & Short Term Investments']]
        CRN = CR.rename(
            columns={'Total Current Liabilities': 'TCL', 'Cash, Cash Equivalents & Short Term Investments': 'C'})
        CRN['Cash Ratio'] = CRN['C'] / CRN['TCL']
        return CRN[['Cash Ratio']]

def ROE(symbol, int='quarterly'):
        Df = fin_st(symbol, 'balance', int)
        Df2 = fin_st(symbol, 'income', 'ttm')
        ROE = Df[['Total Assets', 'Total Liabilities']]
        ROE['NI'] = Df2['Net Income']
        ROEN = ROE.rename(columns={'Total Assets': 'TA', 'Total Liabilities': 'TL'})
        ROEN['BV'] = ROEN['TA'] - ROEN['TL']
        ROEN['ROE'] = (ROEN['NI'] / ROEN['BV'])
        print(ROEN)
        return ROEN[['ROE']]
#TTM net icome no coincide

def Valuation_Ratio(symbol):
    Df   = fin_st(symbol, 'income', 'ttm')
    Df2  = fin_st(symbol,'daly_price','daily')
    VR   = Df[['Net Income (Common)','Shares (Diluted)']]
    Price= Df2['Close']
    VR   = VR.rename(columns={'Net Income (Common)':'NIC','Shares (Diluted)':'SD'})
    EPS  = (VR['NIC'])/(VR['SD'])
    VRN  = sf.reindex(df_src=EPS,df_target=Df2, method='ffill')
    VRN['VRN']= Price/VRN
    return VRN['VRN']

def Gross_Margin(symbol, int='quarterly'):
    Df = fin_st(symbol, 'income', int)
    GM = Df[['Revenue', 'Gross Profit']]
    GMN = GM.rename(columns={'Revenue': 'R', 'Gross Profit': 'GP'})
    GMN['GROSS MARGIN'] = GMN['GP'] / GMN['R']
    return GMN[['GROSS MARGIN']]

def Oper_Margin(symbol, int='quarterly'):
    Df = fin_st(symbol, 'income', int)
    OP = Df[['Operating Income (Loss)', 'Revenue']]
    OPN = OP.rename(columns={'Operating Income (Loss)': 'OP', 'Revenue': 'R'})
    OPN['OPERATING MARGIN'] = OPN['OP'] / OPN['R']
    return OPN[['OPERATING MARGIN']]

def Net_Prof_Margin(symbol, int='quarterly'):
    Df = fin_st(symbol, 'income', int)
    NPM = Df[['Net Income', 'Revenue']]
    NPMN = NPM.rename(columns={'Net Income': 'NI', 'Revenue': 'R'})
    NPMN['NET PROFIT MARGIN'] = NPMN['NI'] / NPMN['R']
    return NPMN[['NET PROFIT MARGIN']]

def To_csv(symbol):
    DataFrame = pd.concat([Current_Ratio(symbol), Cash_Ratio(symbol), Gross_Margin(symbol), Oper_Margin(symbol),Net_Prof_Margin(symbol)],axis=1)
   #CUIDADO
    DataFrame.to_csv (r'G:\Shared drives\Finance Project\Documentos de soporte\Expertise Tecnología\CSV_Ratios.csv', encoding='utf-8', float_format='%.4f', mode="w", index = True, header=True)
    return (DataFrame)

print(ROE('AAPL'))