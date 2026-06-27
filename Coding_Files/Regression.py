#Import required packages
import pandas as pd #for tabular dataframes
import numpy as np #for numerical operations, i.e. arrays
import math as m #for general math function
import statsmodels.api as sm #for OLS regression
import seaborn as sns #for visualization
import warnings #for output cleaning purposes

# Load cleaned dataset
df = pd.read_excel("Outputs&ExcelFiles/3DataRegression.xlsx") #set path to dataset file

# Display first few observations to verify dataset imported correctly
print(df.head()) #check if data is read

# Check variable types to ensure numerical variables are stored correctly
print(df.dtypes) #check if data is in integers/floats format

# Check for zero or negative values before log transformation
# Logarithms are undefined for values less than or equal to zero
#check if there are any 0s in data
print((df['Tomatometer Reviews'] <= 0).sum())
print((df['Opening'] <= 0).sum())
print((df['Budget'] <= 0).sum())


# Apply natural logarithm transformations
# Logs reduce skewness and allow coefficients to be interpreted as elasticities
df['ln_Opening_Weekend_Gross'] = np.log(df['Opening']) #create new column for log of opening weekend gross
df['ln_Budget'] = np.log(df['Budget']) #create new column for log of budget
df['ln_Number_of_Reviews'] = np.log(df['Tomatometer Reviews']) #create new column for log of number of reviews


# Create a dataframe containing only variables used in the regression models
#Create new dataframe for regression analysis
reg_df = df[['ln_Opening_Weekend_Gross',
             'Tomatometer',
             'ln_Number_of_Reviews',
             'Franchise',
             'ln_Budget',
             't']]


# Generate summary statistics for all regression variables
print(reg_df.describe()) #print descriptive statistics of data

# Examine pairwise correlations between variables
corr = reg_df.corr(numeric_only=True) #create correlation matrix
print(corr.round(3))

#Regression Model 1
# Model 1 estimates the bivariate relationship between
# critical reception (Tomatometer score) and opening weekend revenue

X1 = reg_df[['Tomatometer']]
X1 = sm.add_constant(X1)

y = reg_df['ln_Opening_Weekend_Gross']

model1 = sm.OLS(y, X1).fit()

print(model1.summary())

#Regression Model 2
# Add review volume as a control variable

X2 = reg_df[['Tomatometer',
            'ln_Number_of_Reviews']]

X2 = sm.add_constant(X2)

model2 = sm.OLS(y, X2).fit()

print(model2.summary())

#Regression Model 3
# Full regression model including all control variables

X3 = reg_df[['Tomatometer',
            'ln_Number_of_Reviews',
            'Franchise',
            'ln_Budget',
            't']]

X3 = sm.add_constant(X3)


# HC3 robust standard errors are used to correct for heteroskedasticity
model3 = sm.OLS(y, X3).fit(cov_type='HC3')

print(reg_df.describe())
print(model3.summary())

#Check VIF (Multicollinearity)
# Variance Inflation Factors (VIF)
# Used to assess whether explanatory variables are highly correlated

from statsmodels.stats.outliers_influence import variance_inflation_factor
X_vif = reg_df[['Tomatometer',
                'ln_Number_of_Reviews',
                'Franchise',
                'ln_Budget',
                't']]

vif = pd.DataFrame()
vif['Variable'] = X_vif.columns

vif['VIF'] = [
    variance_inflation_factor(X_vif.values, i)
    for i in range(X_vif.shape[1])
]

print(vif)

# Compare explanatory power across specifications
print("Model 1 Adj R²:", model1.rsquared_adj)
print("Model 2 Adj R²:", model2.rsquared_adj)
print("Model 3 Adj R²:", model3.rsquared_adj)
print("Number of observations:", len(reg_df))

# Restrict sample to franchise films only
df_franchise = reg_df[reg_df['Franchise'] == 1]
X4= df_franchise[['Tomatometer',
                  'ln_Number_of_Reviews',
                  'ln_Budget',
                  't']]

X4= sm.add_constant(X4)
y = df_franchise['ln_Opening_Weekend_Gross']

model_f = sm.OLS(y, X4).fit(cov_type='HC3')
print(model_f.summary())


# Restrict sample to standalone films only
df_nonfranchise = reg_df[reg_df['Franchise'] == 0]
X5 = df_nonfranchise[['Tomatometer',
                      'ln_Number_of_Reviews',
                      'ln_Budget',
                      't']]

X5 = sm.add_constant(X5)
y = df_nonfranchise['ln_Opening_Weekend_Gross']

model_nf = sm.OLS(y, X5).fit(cov_type='HC3')
print(model_nf.summary())

# Create interaction term
# Measures whether the effect of Tomatometer differs
# between franchise and non-franchise films
# Interaction term: Tomatometer × Franchise
df['Tomatometer_Franchise'] = df['Tomatometer'] * df['Franchise']

# Define dependent variable
y = df['ln_Opening_Weekend_Gross']

# Full interaction specification
# Define regressors (full model with interaction)
X_int = df[[
    'Tomatometer',
    'Franchise',
    'Tomatometer_Franchise',
    'ln_Number_of_Reviews',
    'ln_Budget',
    't'
]]

# Add constant
X_int = sm.add_constant(X_int)

# Fit model with robust standard errors (important)
interaction_model = sm.OLS(y, X_int).fit(cov_type='HC3')

# Output results
print(interaction_model.summary())