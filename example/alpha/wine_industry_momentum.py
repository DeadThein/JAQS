# -*- encoding: utf-8 -*-

import time

from jaqs.data import RemoteDataService
from jaqs.trade import AlphaBacktestInstance

import jaqs.util as jutil
from jaqs.trade import PortfolioManager
import jaqs.trade.analyze as ana
from jaqs.trade import AlphaStrategy
from jaqs.trade import AlphaTradeApi
from jaqs.trade import model
from jaqs.data import DataView

from config_path import DATA_CONFIG_PATH, TRADE_CONFIG_PATH
data_config = jutil.read_json(DATA_CONFIG_PATH)
trade_config = jutil.read_json(TRADE_CONFIG_PATH)

dataview_dir_path = '../../output/wine_industry_momentum/dataview'
backtest_result_dir_path = '../../output/wine_industry_momentum'

BENCHMARK = '399997.SZ'


def test_save_dataview():
    ds = RemoteDataService()
    ds.init_from_config(data_config)
    dv = DataView()

    props = {'start_date': 20170101, 'end_date': 20171001, 'universe': BENCHMARK,
             'fields': 'close,volume,sw1',
             'freq': 1}

    dv.init_from_config(props, ds)
    dv.prepare_data()

    dv.add_formula('ret', 'Return(close_adj, 20)', is_quarterly=False)
    dv.add_formula('rank_ret', 'Rank(ret)', is_quarterly=False)

    dv.save_dataview(folder_path=dataview_dir_path)


def my_selector(context, user_options=None):
    rank_ret = context.snapshot['rank_ret']

    return rank_ret >= 0.9


def test_alpha_strategy_dataview():
    dv = DataView()
    dv.load_dataview(folder_path=dataview_dir_path)

    props = {
        "benchmark": BENCHMARK,
        "universe": ','.join(dv.symbol),

        "start_date": dv.start_date,
        "end_date": dv.end_date,

        "period": "day",
        "days_delay": 0,

        "init_balance": 1e8,
        "position_ratio": 1.0,
    }
    props.update(data_config)
    props.update(trade_config)

    trade_api = AlphaTradeApi()

    stock_selector = model.StockSelector()
    stock_selector.add_filter(name='rank_ret_top10', func=my_selector)

    strategy = AlphaStrategy(stock_selector=stock_selector, pc_method='equal_weight')
    pm = PortfolioManager()

    bt = AlphaBacktestInstance()
    
    context = model.Context(dataview=dv, instance=bt, strategy=strategy, trade_api=trade_api, pm=pm)
    stock_selector.register_context(context)
    
    bt.init_from_config(props)
    bt.run_alpha()

    bt.save_results(folder_path=backtest_result_dir_path)
    

def test_backtest_analyze():
    ta = ana.AlphaAnalyzer()
    dv = DataView()
    dv.load_dataview(folder_path=dataview_dir_path)

    ta.initialize(dataview=dv, file_folder=backtest_result_dir_path)
    
    ta.do_analyze(result_dir=backtest_result_dir_path, selected_sec=list(ta.universe)[:3],
                  brinson_group='sw1')


if __name__ == "__main__":
    t_start = time.time()

    # test_save_dataview()
    # test_alpha_strategy_dataview()
    test_backtest_analyze()

    t3 = time.time() - t_start
    print "\n\n\nTime lapsed in total: {:.1f}".format(t3)
