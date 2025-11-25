use polars::prelude::*;

fn main() {
    let df = df!(
        "a" => &[1, 2, 3],
        "b" => &["a", "b", "c"]
    )
    .unwrap();

    let filter_series = Series::new("filter", &["a", "c"]);

    let filtered_df = df
        .lazy()
        .filter(col("b").is_in(lit(filter_series)))
        .collect();

    println!("{:?}", filtered_df);
}