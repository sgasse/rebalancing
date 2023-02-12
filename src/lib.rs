use itertools::Itertools;
use prettytable::format;
use prettytable::{row, Table};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub type Error = Box<dyn std::error::Error>;

#[allow(non_snake_case)]
#[derive(Debug, Deserialize, Serialize)]
pub struct Stock {
    pub WKN: String,
    pub ISIN: String,
    pub Price: f64,
    pub Shares: i32,
    pub GoalRatio: f64,
    pub Symbol: String,
}

#[allow(non_snake_case)]
#[derive(Debug, Deserialize, Serialize)]
pub struct Portfolio {
    pub Stocks: Vec<Stock>,
}

pub fn calculate_optimal_reinvest(
    portfolio: &Portfolio,
    reinvest_amount: f64,
    no_selling: bool,
) -> Result<(f64, HashMap<String, i32>), Error> {
    let (selected_stocks, fractional_new_amounts) =
        get_fractional_reinvest_amounts(portfolio, reinvest_amount, no_selling);
    let rounding_combis = get_rounding_combinations(selected_stocks.len());

    let (optimal_new_amounts, optimal_reinvest) = rounding_combis
        .iter()
        .filter_map(|combi| {
            let rounded_new_amounts = combi
                .iter()
                .zip(fractional_new_amounts.iter())
                .map(|(round_up, new_amount)| match round_up {
                    true => new_amount.ceil(),
                    false => new_amount.floor(),
                })
                .collect_vec();

            let reinvest_sum: f64 = rounded_new_amounts
                .iter()
                .zip(selected_stocks.iter())
                .map(|(new_amount, stock)| new_amount * stock.Price)
                .sum();

            match reinvest_sum > reinvest_amount {
                true => None,
                false => Some((rounded_new_amounts, reinvest_sum)),
            }
        })
        .max_by(|a, b| a.1.total_cmp(&b.1))
        .ok_or::<Error>(simple_error::simple_error!("No optimal new amounts found").into())?;

    let new_amounts_map: HashMap<String, i32> = selected_stocks
        .iter()
        .zip(optimal_new_amounts.iter())
        .map(|(stock, new_amount)| (stock.WKN.clone(), *new_amount as i32))
        .collect();
    Ok((optimal_reinvest, new_amounts_map))
}

pub fn print_reinvest(
    portfolio: &Portfolio,
    new_amounts_map: &HashMap<String, i32>,
    optimal_reinvest: f64,
) {
    let actual_sum = portfolio.Stocks.iter().fold(0.0, |acc, elem| {
        acc + elem.Price * (elem.Shares + new_amounts_map.get(&elem.WKN).unwrap_or(&0)) as f64
    });

    let mut table = Table::new();
    table.set_titles(row![
        "WKN",
        "Price",
        "Shares",
        "New Shares",
        "Goal Ratio",
        "Actual Ratio"
    ]);

    for stock in portfolio.Stocks.iter() {
        let new_amount = new_amounts_map.get(&stock.WKN).unwrap_or(&0);
        let actual_ratio = (stock.Price * (stock.Shares + new_amount) as f64) / actual_sum;
        table.add_row(row![
            stock.WKN,
            stock.Price,
            stock.Shares,
            new_amount,
            format!("{:.4}", stock.GoalRatio),
            format!("{actual_ratio:.4}"),
        ]);
    }
    table.set_format(*format::consts::FORMAT_NO_BORDER);

    println!("\n{table}\nWould reinvest {optimal_reinvest:.2}\n");
}

fn get_fractional_reinvest_amounts(
    portfolio: &Portfolio,
    reinvest: f64,
    no_selling: bool,
) -> (Vec<&Stock>, Vec<f64>) {
    let mut selected_stocks = portfolio.Stocks.iter().collect_vec();

    let new_amounts = loop {
        let selected_sum = selected_stocks
            .iter()
            .fold(0.0, |acc, &elem| acc + elem.Price * (elem.Shares as f64));
        let goal_sum = selected_sum + reinvest;

        let ratio_sum = selected_stocks
            .iter()
            .fold(0.0, |acc, &elem| acc + elem.GoalRatio);

        let goal_amounts = selected_stocks
            .iter()
            .map(|&share| ((share.GoalRatio / ratio_sum) * goal_sum) / share.Price)
            .collect_vec();

        let new_amounts = selected_stocks
            .iter()
            .zip(goal_amounts.iter())
            .map(|(&stock, goal_amount)| goal_amount - stock.Shares as f64)
            .collect_vec();

        if no_selling {
            // Find set of stocks for which we buy a positive amount
            let new_selected_stocks = selected_stocks
                .iter()
                .zip(new_amounts.iter())
                .filter_map(|(&stock, &new_amount)| match new_amount > 0.0 {
                    true => Some(stock),
                    false => {
                        log::debug!(
                            "Stock {} would have negative amount {:.3} and will be excluded",
                            stock.WKN,
                            new_amount
                        );
                        None
                    }
                })
                .collect_vec();

            // If the set is not the same, re-enter the loop of calculating amounts
            if new_selected_stocks.len() != selected_stocks.len() {
                selected_stocks = new_selected_stocks;
                continue;
            }
        }

        break new_amounts;
    };

    (selected_stocks, new_amounts)
}

fn get_rounding_combinations(length: usize) -> Vec<Vec<bool>> {
    let limit_number = (2_usize).pow(length as u32);

    (0..limit_number)
        // Map to binary representation with length "length"
        .map(|num| format!("{num:0length$b}"))
        // Map to vector of booleans
        .map(|combi_string| {
            combi_string
                .chars()
                .map(|c| !matches!(c, '0'))
                .collect_vec()
        })
        .collect()
}
