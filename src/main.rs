use clap::Parser;
use rebalancing::{calculate_optimal_reinvest, print_reinvest, Error, Portfolio};
use std::fs::File;

#[derive(Parser, Debug)]
#[clap(author, version)]
struct Args {
    /// Path of portfolio file
    #[clap(long, default_value = "myPortfolio_sorted.json")]
    file: String,

    /// Amount to reinvest
    #[clap(long, default_value_t = 10000.0)]
    reinvest: f64,

    /// Prohibit selling of stocks
    #[clap(long, action)]
    no_selling: bool,
}

fn main() -> Result<(), Error> {
    let args = Args::parse();

    env_logger::builder()
        .format_timestamp(Some(env_logger::TimestampPrecision::Millis))
        .init();

    let portfolio_file = File::open(args.file)?;
    let portfolio: Portfolio = serde_json::from_reader(portfolio_file)?;

    let (optimal_reinvest, new_amounts_map) =
        calculate_optimal_reinvest(&portfolio, args.reinvest, args.no_selling)?;

    print_reinvest(&portfolio, &new_amounts_map, optimal_reinvest);

    Ok(())
}
