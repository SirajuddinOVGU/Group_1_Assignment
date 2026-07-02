#Import required packages
import pandas as pd  # for tabular dataframes
import numpy as np  # for numerical operations, i.e. arrays
import statsmodels.api as sm  # for OLS regression
from statsmodels.stats.outliers_influence import variance_inflation_factor
from pathlib import Path

# Output Setup
OUTPUT_DIR = Path("Outputs&ExcelFiles/RegressionOutput")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

log_path = OUTPUT_DIR / "regression_summaries.txt"
log_lines = []

def log_summary(title: str, model) -> None:
    """Print a model's summary to the terminal AND store it so it can
    be written to the .txt log at the end."""
    text = f"\n{'='*80}\n{title}\n{'='*80}\n{model.summary().as_text()}\n"
    print(text)
    log_lines.append(text)


# Step 1: Load cleaned dataset
df = pd.read_excel("Outputs&ExcelFiles/DataPrep/3DataRegression.xlsx")

print(df.head())  # check if data is read
print(df.dtypes)  # check if data is in integers/floats format

# Check for zero or negative values before log transformation
n_bad_reviews = (df['Tomatometer Reviews'] <= 0).sum()
n_bad_opening = (df['Opening'] <= 0).sum()
n_bad_budget = (df['Budget'] <= 0).sum()
print(f"Non-positive Tomatometer Reviews: {n_bad_reviews}")
print(f"Non-positive Opening: {n_bad_opening}")
print(f"Non-positive Budget: {n_bad_budget}")

n_bad_total = n_bad_reviews + n_bad_opening + n_bad_budget
if n_bad_total > 0:
    before = len(df)
    df = df[(df['Tomatometer Reviews'] > 0) &
            (df['Opening'] > 0) &
            (df['Budget'] > 0)].copy()
    print(f"Dropped {before - len(df)} row(s) with non-positive values "
          f"before log transformation. {len(df)} rows remain.")


# Step 2: Apply natural logarithm transformations
df['ln_Opening_Weekend_Gross'] = np.log(df['Opening'])
df['ln_Budget'] = np.log(df['Budget'])
df['ln_Number_of_Reviews'] = np.log(df['Tomatometer Reviews'])

# Create a dataframe containing only variables used in the regression models
reg_df = df[['ln_Opening_Weekend_Gross',
             'Tomatometer',
             'ln_Number_of_Reviews',
             'Franchise',
             'ln_Budget',
             't']]

print(reg_df.describe())  # descriptive statistics

corr = reg_df.corr(numeric_only=True)
print(corr.round(3))

# Step 3: Regression Model 1
# Bivariate relationship between critical reception (Tomatometer) and opening weekend revenue.
X1 = sm.add_constant(reg_df[['Tomatometer']])
y = reg_df['ln_Opening_Weekend_Gross']
model1 = sm.OLS(y, X1).fit()
log_summary("MODEL 1: Tomatometer only", model1)


# Step 4: Regression Model 2
# Add review volume as a control
X2 = sm.add_constant(reg_df[['Tomatometer', 'ln_Number_of_Reviews']])
model2 = sm.OLS(y, X2).fit()
log_summary("MODEL 2: + Number of Reviews", model2)


# Step 5: Regression Model 3
# Full model with all controls
# HC3 robust standard errors correct for heteroskedasticity
X3 = sm.add_constant(reg_df[['Tomatometer', 'ln_Number_of_Reviews',
                              'Franchise', 'ln_Budget', 't']])
model3 = sm.OLS(y, X3).fit(cov_type='HC3')
log_summary("MODEL 3: Full model (HC3 robust SE)", model3)


# Step 6: VIF (multicollinearity check)
X_vif = sm.add_constant(reg_df[['Tomatometer', 'ln_Number_of_Reviews',
                                 'Franchise', 'ln_Budget', 't']])
vif = pd.DataFrame()
vif['Variable'] = X_vif.columns
vif['VIF'] = [variance_inflation_factor(X_vif.values, i)
              for i in range(X_vif.shape[1])]
vif = vif[vif['Variable'] != 'const'].reset_index(drop=True)
print(vif)

# Compare explanatory power across specifications
print("Model 1 Adj R\u00b2:", model1.rsquared_adj)
print("Model 2 Adj R\u00b2:", model2.rsquared_adj)
print("Model 3 Adj R\u00b2:", model3.rsquared_adj)
print("Number of observations:", len(reg_df))


# Step 7: Franchise-only and non-franchise-only subsamples
df_franchise = reg_df[reg_df['Franchise'] == 1]
X4 = sm.add_constant(df_franchise[['Tomatometer', 'ln_Number_of_Reviews',
                                    'ln_Budget', 't']])
y_franchise = df_franchise['ln_Opening_Weekend_Gross']
model_f = sm.OLS(y_franchise, X4).fit(cov_type='HC3')
log_summary("MODEL: Franchise films only (HC3 robust SE)", model_f)

df_nonfranchise = reg_df[reg_df['Franchise'] == 0]
X5 = sm.add_constant(df_nonfranchise[['Tomatometer', 'ln_Number_of_Reviews',
                                       'ln_Budget', 't']])
y_nonfranchise = df_nonfranchise['ln_Opening_Weekend_Gross']
model_nf = sm.OLS(y_nonfranchise, X5).fit(cov_type='HC3')
log_summary("MODEL: Non-franchise films only (HC3 robust SE)", model_nf)


# Step 8: Interaction model
# Tests whether the effect of Tomatometer differs between franchise and non-franchise films.
df['Tomatometer_Franchise'] = df['Tomatometer'] * df['Franchise']
y_full = df['ln_Opening_Weekend_Gross']
X_int = sm.add_constant(df[['Tomatometer', 'Franchise',
                             'Tomatometer_Franchise',
                             'ln_Number_of_Reviews', 'ln_Budget', 't']])
interaction_model = sm.OLS(y_full, X_int).fit(cov_type='HC3')
log_summary("MODEL: Full interaction model (HC3 robust SE)", interaction_model)


# Step 9: Save Output
# Two output format (txt and Excel)
log_path.write_text("\n".join(log_lines), encoding="utf-8")
print(f"Saved full regression summaries to: {log_path}")


def tidy_results(model, label: str) -> pd.DataFrame:
    """Turn a fitted statsmodels model into a tidy coefficient table."""
    ci = model.conf_int()
    return pd.DataFrame({
        "model": label,
        "variable": model.params.index,
        "coef": model.params.values,
        "std_err": model.bse.values,
        "t_or_z": model.tvalues.values,
        "p_value": model.pvalues.values,
        "ci_low": ci[0].values,
        "ci_high": ci[1].values,
    })


models_to_save = {
    "Model1_Tomatometer": model1,
    "Model2_AddReviews": model2,
    "Model3_FullModel": model3,
    "Franchise_Only": model_f,
    "NonFranchise_Only": model_nf,
    "Interaction_Model": interaction_model,
}

comparison_rows = []
for label, m in models_to_save.items():
    comparison_rows.append({
        "model": label,
        "n_obs": int(m.nobs),
        "rsquared": round(m.rsquared, 4),
        "rsquared_adj": round(m.rsquared_adj, 4),
    })
comparison_df = pd.DataFrame(comparison_rows)

excel_path = OUTPUT_DIR / "regression_results.xlsx"
with pd.ExcelWriter(excel_path) as writer:
    comparison_df.to_excel(writer, sheet_name="Model_Comparison", index=False)
    vif.to_excel(writer, sheet_name="VIF", index=False)
    for label, m in models_to_save.items():
        tidy_results(m, label).to_excel(writer, sheet_name=label[:31], index=False)
        # Excel sheet names are capped at 31 characters -- label[:31]
        # guards against a ValueError if a model name ever gets longer.

print(f"Saved tidy regression results to: {excel_path}")