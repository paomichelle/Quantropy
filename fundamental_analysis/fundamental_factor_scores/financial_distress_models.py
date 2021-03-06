import math
import os
import pickle
from datetime import datetime, timedelta
import fundamental_analysis.financial_statements_entries as financials
import fundamental_analysis.supporting_metrics as metrics
import fundamental_analysis.accounting_ratios as ratios
import numpy as np
import config
from macroeconomic_analysis import macroeconomic_analysis


def piotroski_f_score(stock: str, date: datetime = datetime.now(), lookback_period: timedelta = timedelta(days=0),
                      period: str = 'TTM', diluted_shares=True):
    piotroski_dictio = {
        'Profitability': {},
        'Financial Leverage, Liquidity, and Source of Funds': {},
        'Operating Efficiency': {},
        'Piotroski F-Score': {' ': {' ': {0}}}
    }

    # Return on Assets (1 point if it is positive in the current year, 0 otherwise)
    return_on_assets_current_year = ratios.return_on_assets(stock=stock, date=date, lookback_period=lookback_period,
                                                            period=period)
    piotroski_dictio['Profitability']['Return on Assets'] = {
        'Return on Assets Current Year': '{:.4f}'.format(return_on_assets_current_year),
        'ROA Positive in the Current Year ?': return_on_assets_current_year > 0}

    # Operating Cash Flow (1 point if it is positive in the current year, 0 otherwise)
    operating_cash_flow_current_year = financials.cash_flow_operating_activities(stock=stock, date=date,
                                                                                 lookback_period=lookback_period,
                                                                                 period=period)
    piotroski_dictio['Profitability']['Operating Cash Flow'] = {
        'Operating Cash Flow Current Year': '{:.2f}'.format(operating_cash_flow_current_year),
        'OCF Positive in the Current Year ?': operating_cash_flow_current_year > 0}

    # Change in Return of Assets (ROA) (1 point if ROA is higher in the current year compared to the previous one,
    # 0 otherwise)
    return_on_assets_previous_year = ratios.return_on_assets(stock=stock, date=date,
                                                             lookback_period=timedelta(days=365), period=period)
    piotroski_dictio['Profitability']['Change in Return of Assets'] = {
        'Return on Assets Current Year': '{:.4f}'.format(return_on_assets_current_year),
        'Return on Assets Previous Year': '{:.4f}'.format(return_on_assets_previous_year),
        'ROA Current Year > ROA Previous Year ?': return_on_assets_current_year > return_on_assets_previous_year}

    # Accruals (1 point if Operating Cash Flow/Total Assets is higher than ROA in the current year, 0 otherwise)
    total_assets_current_year = financials.total_assets(stock=stock, date=date, lookback_period=lookback_period,
                                                        period=period)
    accruals = operating_cash_flow_current_year / total_assets_current_year
    piotroski_dictio['Profitability']['Accruals'] = {
        'Operating Cash Flow Current Year': '{}'.format(operating_cash_flow_current_year),
        'Total Assets Current Year': '{}'.format(total_assets_current_year),
        'Accruals Current Year': '{:.4f}'.format(accruals),
        'ROA Current Year': '{:.4f}'.format(return_on_assets_current_year),
        'Accruals Current Year > ROA Current Year ?': accruals > return_on_assets_current_year}

    # Change in Leverage (long-term) ratio (1 point if the ratio is lower this year compared to the previous one,
    # 0 otherwise)
    debt_to_assets_current_year = ratios.debt_ratio(stock=stock, date=date, lookback_period=lookback_period,
                                                    period=period)
    debt_to_assets_previous_year = ratios.debt_ratio(stock=stock, date=date, lookback_period=timedelta(days=365),
                                                     period=period)
    piotroski_dictio['Financial Leverage, Liquidity, and Source of Funds'][
        'Change in Leverage Ratio'] = {'Debt to Assets Current Year': '{:.4f}'.format(debt_to_assets_current_year),
                                       'Debt to Assets Previous Year': '{:.4f}'.format(debt_to_assets_current_year),
                                       'D/A Current Year < D/A Previous Year ?': debt_to_assets_current_year < debt_to_assets_previous_year}

    # Change in Current ratio (1 point if it is higher in the current year compared to the previous one, 0 otherwise)
    current_ratio_current_year = ratios.current_ratio(stock=stock, date=date, lookback_period=lookback_period,
                                                      period=period)
    current_ratio_previous_year = ratios.current_ratio(stock=stock, date=date, lookback_period=timedelta(days=365),
                                                       period=period)
    piotroski_dictio['Financial Leverage, Liquidity, and Source of Funds'][
        'Change in Current Ratio'] = {'Current Ratio Current Year': '{:.4f}'.format(current_ratio_current_year),
                                      'Current Ratio Previous Year': '{:.4f}'.format(current_ratio_previous_year),
                                      'CR Current Year > CR Previous Year ?': current_ratio_current_year > current_ratio_previous_year}

    shares_current_year = financials.total_shares_outstanding(stock=stock, date=date, lookback_period=lookback_period,
                                                              diluted_shares=diluted_shares, period=period)
    shares_previous_year = financials.total_shares_outstanding(stock=stock, date=date,
                                                               lookback_period=timedelta(days=365),
                                                               diluted_shares=diluted_shares, period=period)
    # Change in the number of shares (1 point if no new shares were issued during the last year)
    piotroski_dictio['Financial Leverage, Liquidity, and Source of Funds'][
        'Change in Number of Shares'] = {'Shares Outstanding Current Year': shares_current_year,
                                         'Shares Outstanding Previous Year': shares_previous_year,
                                         'No New Shares Issued ?': shares_current_year <= shares_previous_year}

    # Change in Gross Margin (1 point if it is higher in the current year compared to the previous one, 0 otherwise)
    gross_margin_current_year = ratios.gross_profit_margin(stock=stock, date=date, lookback_period=lookback_period,
                                                           period=period)
    gross_margin_previous_year = ratios.gross_profit_margin(stock=stock, date=date, lookback_period=timedelta(days=365),
                                                            period=period)

    piotroski_dictio['Operating Efficiency']['Gross Margin'] = {
        'Gross Margin Current Year': '{:.4f}'.format(gross_margin_current_year),
        'Gross Margin Previous Year': '{:.4f}'.format(gross_margin_previous_year),
        'GM Current Year > GM Previous Year ?': gross_margin_current_year > gross_margin_previous_year}

    # Change in Asset Turnover ratio (1 point if it is higher in the current year compared to the previous one,
    # 0 otherwise)
    asset_turnover_current_year = ratios.asset_turnover_ratio(stock=stock, date=date, lookback_period=lookback_period,
                                                              period=period)
    asset_turnover_previous_year = ratios.asset_turnover_ratio(stock=stock, date=date,
                                                               lookback_period=timedelta(days=365), period=period)
    piotroski_dictio['Operating Efficiency']['Asset Turnover Ratio'] = {
        'Asset Turnover Ratio Current Year': '{:.4f}'.format(asset_turnover_current_year),
        'Asset Turnover Ratio Previous Year': '{:.4f}'.format(asset_turnover_previous_year),
        'ATO Current Year > ATO Previous Year ?': asset_turnover_current_year > asset_turnover_previous_year}

    number_of_trues = 0
    for k, v in piotroski_dictio.items():
        for kk, vv in v.items():
            for kkk, vvv in vv.items():
                if isinstance(vvv, np.bool_) and vvv:
                    number_of_trues = number_of_trues + 1

    piotroski_dictio['Piotroski F-Score'][' '][' '] = number_of_trues

    return piotroski_dictio


def probability_of_bankruptcy(score):
    return math.exp(score) / (1 + math.exp(score))


def altman_z_score(stock: str, date: datetime = datetime.now(), lookback_period: timedelta = timedelta(days=0),
                   period: str = 'TTM'):
    A = metrics.net_working_capital(stock=stock, date=date, lookback_period=lookback_period, period=period) \
        / financials.total_assets(stock=stock, date=date, lookback_period=lookback_period, period=period)
    B = financials.retained_earnings(stock=stock, date=date, lookback_period=lookback_period, period=period) \
        / financials.total_assets(stock=stock, date=date, lookback_period=lookback_period, period=period)
    C = metrics.earnings_before_interest_and_taxes(stock=stock, date=date, lookback_period=lookback_period,
                                                   period=period) \
        / financials.total_assets(stock=stock, date=date, lookback_period=lookback_period, period=period)
    D = financials.total_shareholders_equity(stock=stock, date=date, lookback_period=lookback_period, period=period) \
        / financials.total_liabilities(stock=stock, date=date, lookback_period=lookback_period, period=period)
    E = financials.net_sales(stock=stock, date=date, lookback_period=lookback_period, period=period) \
        / financials.total_assets(stock=stock, date=date, lookback_period=lookback_period, period=period)

    with open(os.path.join(config.ROOT_DIR, config.DATA_DIR_NAME, config.MARKET_TICKERS_DIR_NAME, "nasdaq_df.pickle"),
              "rb") as f:
        nasdaq_tickers = pickle.load(f).index

    # for private manufacturing companies
    if stock not in nasdaq_tickers and 'Manufacturing' not in metrics.get_stock_sector(stock):
        z_plus_score = 0.717 * A + 0.847 * B + 3.107 * C + 0.420 * D + 0.998 * E
        if z_plus_score > 2.9:
            return z_plus_score, 'safe zone'
        elif z_plus_score < 1.23:
            return z_plus_score, 'distress zone'
        else:
            return z_plus_score, 'grey zone'

    # for foreign firms (i.e. all but US and Canada) and for non-manufacturing firms, both public and private
    elif ('Other Countries' in metrics.get_stock_location(stock)) \
            or ('Manufacturing' not in metrics.get_stock_sector(stock)):

        if 'Other Countries' in metrics.get_stock_location(stock):
            z_plus_plus_score = 3.25 + 6.56 * A + 3.26 * B + 6.72 * C + 1.05 * D

        else:
            z_plus_plus_score = 6.56 * A + 3.26 * B + 6.72 * C + 1.05 * D

        if z_plus_plus_score > 2.6:
            return z_plus_plus_score, 'safe zone'
        elif z_plus_plus_score < 1.1:
            return z_plus_plus_score, 'distress zone'
        else:
            return z_plus_plus_score, 'grey zone'

    else:  # for public manufacturing firms, original score
        D = metrics.market_capitalization(stock=stock, date=date, lookback_period=lookback_period,
                                          period=period) / financials.total_liabilities(stock=stock, date=date,
                                                                                        lookback_period=lookback_period,
                                                                                        period=period)
        z_score = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E
        if z_score > 2.99:
            return z_score, 'safe zone'
        elif z_score < 1.81:
            return z_score, 'distress zone'
        else:
            return z_score, 'grey zone'


def ohlson_o_score(stock: str, date: datetime = datetime.now(), lookback_period: timedelta = timedelta(days=0),
                   period: str = 'TTM'):
    TA = financials.total_assets(stock=stock, date=date, lookback_period=lookback_period, period=period)
    GNP = macroeconomic_analysis.gross_national_product_price_index(date)
    TL = financials.total_liabilities(stock=stock, date=date, lookback_period=lookback_period, period=period)
    WC = metrics.net_working_capital(stock=stock, date=date, lookback_period=lookback_period, period=period)
    CL = financials.current_total_liabilities(stock=stock, date=date, lookback_period=lookback_period, period=period)
    CA = financials.current_total_assets(stock=stock, date=date, lookback_period=lookback_period, period=period)
    X = 1 if TL > TA else 0
    NI = financials.net_income(stock=stock, date=date, lookback_period=lookback_period, period=period)
    NI_prev = financials.net_income(stock=stock, date=date, lookback_period=lookback_period, period=period)
    FFO = financials.cash_flow_operating_activities(stock=stock, date=date, lookback_period=lookback_period,
                                                    period=period)
    Y = 1 if (NI < 0 and NI_prev < 0) else 0
    return -1.32 - 0.407 * np.log(TA / GNP) + 6.03 * (TL / TA) - 1.43 * (WC / TA) + 0.0757 * (CL / CA) - 1.72 * X \
           - 2.37 * (NI / TA) - 1.83 * (FFO / TL) + 0.285 * Y - 0.521 * ((NI - NI_prev) / (abs(NI) + abs(NI_prev)))


# https://scholar.harvard.edu/files/campbell/files/campbellhilscherszilagyi_jf2008.pdf
def campbell_hilscher_szilagyi_model():
    # Net income to market total assets
    NIMTAAVG = 0

    # Total liabilities to market total assets
    TLMTA = 0

    # Cash to market total assets
    CASHMTA = 0

    # Excess return compared to the S&P 500
    EXRETAVG = 0

    # Standard deviation of daily returns over the past three months
    SIGMA = 0

    # Relative size
    RSIZE = 0

    # Market-to-book equity ratio
    MB = 0

    # The log of the stock price, capped at log(15)
    PRICE = 0

    LPFD = -20.12 * NIMTAAVG + 1.60 * TLMTA - 7.88 * EXRETAVG + 1.55 * SIGMA - 0.005 * RSIZE \
           - 2.27 * CASHMTA + 0.070 * MB - 0.09 * PRICE - 8.87

    return probability_of_bankruptcy(LPFD)
