#!/usr/bin/env python3
import json
from argparse import ArgumentParser
from datetime import datetime


def print_portfolio(portfolio: dict):
    """Print portfolio.

    Args:
        portfolio (dict): Portfolio to print.

    """
    print("\nPortfolio:\nWKN    |  now |  new |  price | g_ratio | r_ratio")
    for stock in portfolio["Stocks"]:
        stock_line = (
            f"{stock['WKN']} | {stock['Shares']:4} | {stock.get('NewShares', 0):4} | "
            f"{stock['Price']:6.2f} | {stock['GoalRatio']:7.4f} | "
            f"{stock.get('RebalancedRatio', 0.0):7.4f}"
        )
        print(stock_line)

    value_line = f"Total value: {_calc_total_val(portfolio):9.2f}"
    if "NewShares" in stock:
        value_line += f", reinvest: {_calc_reinvest_val(portfolio):9.2f}"
    print(value_line)


def rebalance_portfolio(portfolio: dict, reinvest: float):
    """Rebalance portfolio.

    Args:
        portfolio (dict): Portfolio to rebalance.
        reinvest (float): Amount of money to reinvest/take out.

    """
    # Sanity checks
    if not valid_portfolio(portfolio):
        return

    # Figure out current portfolio value
    portf_cur_val = _calc_current_val(portfolio)

    # Calculate rounded goal shares
    portf_goal_val = portf_cur_val + reinvest
    for stock in portfolio["Stocks"]:
        stock_goal_value = portf_goal_val * stock["GoalRatio"]

        stock["NewShares"] = round(stock_goal_value / stock["Price"]) - stock["Shares"]

        # Price per partial is an indicator of how much adding/removing a share will
        # affect the goal ratio
        stock["DeltaRatio"] = _delta_ratio(stock, portf_goal_val)

    print_portfolio(portfolio)

    # Adjust rounded goal shares
    # - to get as close as possible towards the reinvest value
    # - to stay below the reinvest value while least disturbing the rebalanced ratio
    _adjust_new_stocks_to_target(portfolio, portf_goal_val)

    print_portfolio(portfolio)

    # TODO: Sort before saving
    pass


def read_json_portfolio(portfolio_file: str) -> dict:
    """Read portfolio from JSON file.

    Args:
        portfolio_file (str): Filepath to read.

    Returns:
        dict: Parsed portfolio.

    """
    with open(portfolio_file, "r") as p_file:
        return json.load(p_file)


def store_rebalanced_portfolio(portfolio: dict, path: str):
    """Store a rebalanced portfolio.

    Args:
        path (str): Path to store the portfolio to.

    """
    # Sort stocks by WKN
    portfolio["Stocks"] = sorted(portfolio["Stocks"], key=lambda x: x["WKN"])

    with open(path, "w") as file_:
        json.dump(portfolio, file_, indent=4)


def valid_portfolio(portfolio: dict) -> bool:
    """Check if a portfolio is valid.

    Args:
        portfolio (dict): Portfolio to check.

    Returns:
        bool: True if the portfolio is value, else False.

    """
    ratio_sum = sum([stock["GoalRatio"] for stock in portfolio["Stocks"]])
    if abs(1.0 - ratio_sum) > 1e-4:
        print(f"Goal ratios of stocks sum up to {ratio_sum} instead of 1.0")
        return False

    if any(
        [
            stock["Price"] is None or stock["Price"] == 0.0
            for stock in portfolio["Stocks"]
        ]
    ):
        print("Some stocks are missing price information")
        return False

    return True


def _adjust_new_stocks_to_target(portfolio: dict, portf_goal_val: float):
    """Adjust the number of new stocks to the target investment value.

    Args:
        portfolio (dict): Portfolio whose stocks to adjust.
        portf_goal_val (float): Goal value of the portfolio after reinvestment.

    """
    # Compute current total value (including reinvest)
    portf_total_val = _calc_total_val(portfolio)

    # Get sorted list of DeltaRatio for all stocks
    ascending_ppp = sorted(portfolio["Stocks"], key=lambda x: x["DeltaRatio"])

    if portf_total_val > portf_goal_val:
        # Need to round down some stock, starting with those least affecting the ratio
        for stock in ascending_ppp:
            stock["NewShares"] -= 1
            portf_total_val -= stock["Price"]
            if portf_total_val < portf_goal_val:
                break
    else:
        # Need to round up some stock, starting with those least affecting the ratio
        for stock in ascending_ppp:
            stock["NewShares"] += 1
            portf_total_val += stock["Price"]
            if portf_total_val > portf_goal_val:
                # Undo last step
                stock["NewShares"] -= 1
                portf_total_val -= stock["Price"]

    _eval_rebalanced_ratio(portfolio, portf_total_val)


def _eval_rebalanced_ratio(portfolio: dict, portf_total_val: float):
    """Evaluate the rebalanced ratio of stocks in a portfolio.

    Args:
        portfolio (dict): Portfolio for which to calculate the rebalanced ratios.
        portf_total_val (float): Sum of current portfolio value and reinvestment.
    """
    for stock in portfolio["Stocks"]:
        stock["RebalancedRatio"] = (
            (stock["Shares"] + stock["NewShares"]) * stock["Price"]
        ) / portf_total_val


def _delta_ratio(stock: dict, portf_goal_val: float) -> float:
    """Calculate derivative of ratio with respect to the new shares.

    Args:
        stock (dict): Stock information.
        portf_goal_val (float): Sum of current portfolio value and reinvestment.

    Returns:
        float: Derivative of ratio with respect to the new shares.

    """
    # ratio = (Shares + NewShares) / (Fixed + (Shares + NewShares) * Price)
    # d/dx (u/v) = (u'v - uv') / v**2
    # delta_ratio = ... = Price * Fixed / (Fixed + (Shares + NewShares) * Price)**2
    # = Price * Fixed / (portf_goal_val)**2

    fixed_part = (
        portf_goal_val - (stock["Shares"] + stock["NewShares"]) * stock["Price"]
    )

    delta_ratio = (stock["Price"] * fixed_part) / portf_goal_val ** 2
    return delta_ratio


def _calc_current_val(portfolio: dict) -> float:
    """Calculate current portfolio value.

    Args:
        portfolio (dict): Portfolio to evaluate.

    Returns:
        float: Current value of the portfolio without reinvestment.

    """
    return sum([stock["Shares"] * stock["Price"] for stock in portfolio["Stocks"]])


def _calc_reinvest_val(portfolio: dict) -> float:
    """Caluclate reinvestment value.

    Args:
        portfolio (dict): Portfolio to evaluate.

    Returns:
        float: Value of the stocks to by.

    """
    return sum([stock["NewShares"] * stock["Price"] for stock in portfolio["Stocks"]])


def _calc_total_val(portfolio: dict) -> float:
    """Calculate total value of the portfolio.

    Args:
        portfolio (dict): Portfolio to evaluate.

    Returns:
        float: Total value of the portfolio.

    """
    if "NewShares" in portfolio["Stocks"][0]:
        return _calc_current_val(portfolio) + _calc_reinvest_val(portfolio)

    return _calc_current_val(portfolio)


def parse_args():
    """Parse arguments."""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(
        help="Print or rebalance a portfolio", dest="command", required=True
    )

    parser_print = subparsers.add_parser("print", help="Print a portfolio")
    parser_print.add_argument(
        "--input", "-i", required=True, help="Input file with portfolio"
    )

    parser_rebalance = subparsers.add_parser("rebalance", help="Rebalance a portfolio")
    parser_rebalance.add_argument(
        "--input", "-i", required=True, help="Input file with portfolio"
    )
    parser_rebalance.add_argument(
        "--reinvest", "-r", type=float, default=0.0, help="Value to reinvest"
    )

    ts = datetime.now().strftime("%Y_%m_%d_%H.%M.%S")
    parser_rebalance.add_argument(
        "--outfile",
        "-o",
        default=f"rebalanced_{ts}.json",
        help="Output file to store rebalanced portfolio",
    )

    return parser.parse_args()


def main():
    """Run main routine."""
    args = parse_args()

    portfolio = read_json_portfolio(args.input)

    if args.command == "rebalance":
        rebalance_portfolio(portfolio, args.reinvest)

        if args.outfile == args.input:
            raise ValueError("Cannot write to input file to prevent accidents!")

        store_rebalanced_portfolio(portfolio, args.outfile)
    elif args.command == "print":
        print_portfolio(portfolio)


if __name__ == "__main__":
    main()
