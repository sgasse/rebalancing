# Portfolio Rebalancing

## Purpose
This repository contains scripts to rebalance a stock portfolio. The ratios of the stock values are given, thus the script shall calculate how many stocks to buy in order to closely match the `goal_ratio` while spending almost exactly the amount `investment`.

## Usage
Provide a `csv` file with the structure of `dummy_data.csv`. You can run the python or Julia version of te script:
```
python3 dummy_data.csv 10000.0
julia dummy_data.csv 10000.0
```

## Implementation
This repository contains a python implementation and a Julia implementation. In my early days of investing, I actually used my python implementation. In order to make some first steps in Julia, I ported the script to the language.

In both scripts, the mathematical idea is the same:
- calculate the current value of the portfolio `portf_val`
- add the amount `investment` to the current value and divide it by the `goal_ratio` values to compute the theoretical values `th_share_values` that should be in the portfolio per stock
- substract the value per stock that you already have from the `stocks` you own to get the theoretical values you want to buy per stock `th_new_values`
- divide the theoretical values by the stock prices to obtain the theoretical number of shares to buy `th_new_shares`
- since you can only buy whole shares and not fractions, exhaustively enumerate all possible cominations of rounding up/down and choose the combination that is the largest still below `investment`

Although I found the Julia package `IterTools`, I was unable to find the functionality I have in the python module `itertools.product`. Consequently, I added a _hacky_ function to provide all possible roundings in Julia with `_append_combis`.

## Conclusion
It took me a little time to port the script and I am probably not using a very _juliaistic_ style of programming. Nevertheless, due to comparable variable and function names, I have a reference how to do certain things that I am used to in python also in Julia.

The main purpose is to rebalance my portfolio once in a while, but not very often. For this task, it is sufficient. However, for more frequent usage, there are way better tools like [PortfolioPerformance](https://github.com/buchen/portfolio) that also allow to include order fees in the calculation. I considered using the [Yahoo Finance API](https://blog.rapidapi.com/how-to-use-the-yahoo-finance-api/) or [Quandl](https://www.quandl.com/) but setting up the free version was not worth the hassle for the few different stock prices.
