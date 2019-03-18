import sys
import itertools

import pandas as pd
import numpy as np

from datetime import datetime


def combi_to_shares(shares, combi):
    shares = shares.copy()
    for ind, val in enumerate(combi):
        if val == 1:
            shares[ind] = np.ceil(shares[ind])
        else:
            shares[ind] = np.floor(shares[ind])
    return shares


def create_share_roundings(shares):
    return [combi_to_shares(shares, combi) for combi in itertools.product(
        [0, 1], repeat=len(shares))]


def calculate_reinvestment_shares(data_file, investment, save=True):
    investment = float(investment)
    pf = pd.read_csv(data_file)

    portf_val = (pf.price * pf.shares).sum()

    th_portf_value = portf_val + investment
    th_share_values = pf.goal_ratio * th_portf_value
    th_new_values = th_share_values - pf.price * pf.shares
    th_new_shares = th_new_values / pf.price

    new_share_options = create_share_roundings(th_new_shares)
    best_investment = 0.0
    for shares in new_share_options:
        cur_investment = (pf.price * shares).sum()
        if cur_investment < investment and cur_investment > best_investment:
            best_shares = shares
            best_investment = cur_investment

    rebalanced_values = (pf.shares + best_shares) * pf.price
    pf['reinvest_shares'] = best_shares.astype(np.int)
    pf['rebalanced_ratio'] = rebalanced_values / rebalanced_values.sum()

    if save == True:
        pd.set_option('precision', 4)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
        out_file = 'data_rebalanced_{}.csv'.format(timestamp)
        pf.to_csv(out_file, sep=',', header=True)
        print("Saved dataframe to {}".format(out_file))
    return pf


if __name__ == "__main__":
    if len(sys.argv) == 3:
        data_file = sys.argv[1]
        investment = sys.argv[2]
        pf = calculate_reinvestment_shares(data_file, investment)
        print(pf)
