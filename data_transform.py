# data_transform.py
import pandas as pd
from pathlib import Path

excel_path = "excel_sample_data_de.xlsx"
output_path = "sql_test-expected_from_python.xlsx"

# 1) Read raw sheet
df = pd.read_excel(excel_path, sheet_name="sql_test-raw")

# 2) Normalize month column into consistent string form for grouping/pivoting
# If month is datetime-like, convert to YYYY-MM-DD; if it's like 'Jan-25', try parsing
if pd.api.types.is_datetime64_any_dtype(df['month']):
    df['month_str'] = pd.to_datetime(df['month']).dt.strftime('%Y-%m-%d')
else:
    # try parse 'Jan-25' as %b-%y first; fall back to generic parse; else keep literal
    parsed = pd.to_datetime(df['month'], format='%b-%y', errors='coerce')
    parsed = parsed.fillna(pd.to_datetime(df['month'], errors='coerce'))
    df['month_str'] = pd.to_datetime(parsed).dt.strftime('%Y-%m-%d')
    df['month_str'] = df['month_str'].fillna(df['month'].astype(str))

# 3) Compute profit
df['profit'] = df['sales_amt'] - df['sales_cost']

# 4) Compute totals per (month_str, category)
totals = df.groupby(['month_str','category'], dropna=False).agg(
    total_sales_qty=('sales_qty','sum'),
    total_sales_amt=('sales_amt','sum'),
    total_sales_cost=('sales_cost','sum'),
    total_profit=('profit','sum')
).reset_index()

# 5) Merge totals to compute contributions
df = df.merge(totals, how='left', on=['month_str','category'])

# safe divide with zero checks
def safe_div(n, d):
    try:
        if pd.isna(d) or d == 0:
            return 0.0
        return n / d
    except Exception:
        return 0.0

df['sales_qty_contribution_by_category'] = df.apply(lambda r: safe_div(r['sales_qty'], r['total_sales_qty']), axis=1)
df['sales_amt_contribution_by_category']  = df.apply(lambda r: safe_div(r['sales_amt'], r['total_sales_amt']), axis=1)
df['sales_cost_contribution_by_category'] = df.apply(lambda r: safe_div(r['sales_cost'], r['total_sales_cost']), axis=1)
df['profit_contribution_by_category']     = df.apply(lambda r: safe_div(r['profit'], r['total_profit']), axis=1)

# Round contributions (4 decimal places to match SQL)
for c in ['sales_qty_contribution_by_category','sales_amt_contribution_by_category',
          'sales_cost_contribution_by_category','profit_contribution_by_category']:
    df[c] = df[c].round(4)

# 6) Pivot to wide format: product, category, then for each month the 4 metrics
metrics = [
    ('sales_qty_contribution_by_category', 'sales qty contribution by category'),
    ('sales_amt_contribution_by_category', 'sales amt contribution by category'),
    ('sales_cost_contribution_by_category', 'sales cost contribution by category'),
    ('profit_contribution_by_category', 'profit contribution by category'),
]

# create a tidy frame with needed columns
tidy = df[['product','category','month_str'] + [m[0] for m in metrics]].copy()

# build pivoted pieces for each metric then join horizontally to get month-blocks
pivot_frames = []
months_order = sorted(tidy['month_str'].unique())

for metric_col, metric_label in metrics:
    p = tidy.pivot(index=['product','category'], columns='month_str', values=metric_col)
    p.columns = [f"{m} {metric_label}" for m in p.columns]
    pivot_frames.append(p)

from functools import reduce
final_wide = reduce(lambda left,right: left.join(right, how='outer'), pivot_frames).reset_index()

# Replace NaNs with 0 for contribution columns (if any)
final_wide = final_wide.fillna(0)

# Reorder columns: product, category, then for month in months_order the 4 metrics
cols = ['product','category']
for m in months_order:
    for _, metric_label in metrics:
        cols.append(f"{m} {metric_label}")
cols = [c for c in cols if c in final_wide.columns]
final_wide = final_wide[cols]

# 7) Save to Excel
final_wide.to_excel(output_path, index=False)
print(f"Saved final output to {output_path}")

# 8) Validation checks: contributions sum approximately 1 for each month+category
# We'll compute per-month+category sums of each metric (they should be ~1.0)
validate = df.groupby(['month_str','category']).agg(
    qty_sum = ('sales_qty_contribution_by_category','sum'),
    amt_sum = ('sales_amt_contribution_by_category','sum'),
    cost_sum = ('sales_cost_contribution_by_category','sum'),
    profit_sum = ('profit_contribution_by_category','sum')
).reset_index()

# print any anomalies where absolute diff from 1 > 0.01 (1% tolerance)
anomalies = validate[
    (validate['qty_sum'].sub(1).abs() > 0.01) |
    (validate['amt_sum'].sub(1).abs() > 0.01) |
    (validate['cost_sum'].sub(1).abs() > 0.01) |
    (validate['profit_sum'].sub(1).abs() > 0.01)
]

print("Validation summary (per month+category sums):")
print(validate.to_string(index=False))
if not anomalies.empty:
    print("\nWarning: Some contribution sums differ from 1 by > 0.01:")
    print(anomalies.to_string(index=False))
else:
    print("\nAll contribution sums are within tolerance.")

# optional: preview top rows
print("\nPreview of final output:")
print(final_wide.head().to_string(index=False))
