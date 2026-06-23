#Import required packages
import pandas as pd #for tabular dataframes
import numpy as np #for numerical operations, i.e. arrays
import math as m #for general math function
import statsmodels.api as sm #for OLS regression
import seaborn as sns #for visualization
import warnings #for output cleaning purposes

df = pd.read_excel("Outputs&ExcelFiles/CleanedRegressionData.xlsx") #set path to dataset file
print(df.head()) #check if data is read

print(df.dtypes) #check if data is in integers/floats format

#check if there are any 0s in data
print((df['Number_of_Reviews'] <= 0).sum())
print((df['Opening_Weekend_Gross'] <= 0).sum())
print((df['Budget'] <= 0).sum())

df['ln_Opening_Weekend_Gross'] = np.log(df['Opening_Weekend_Gross']) #create new column for log of opening weekend gross
df['ln_Budget'] = np.log(df['Budget']) #create new column for log of budget
df['ln_Number_of_Reviews'] = np.log(df['Number_of_Reviews']) #create new column for log of number of reviews

#Create new dataframe for regression analysis
reg_df = df[['ln_Opening_Weekend_Gross',
             'Tomatometer',
             'ln_Number_of_Reviews',
             'Franchise_Status',
             'ln_Budget',
             'Year']]

print(reg_df.describe())

corr = reg_df.corr(numeric_only=True) #create correlation matrix
print(corr.round(3))

X1 = reg_df[['Tomatometer']]
X1 = sm.add_constant(X1)

y = reg_df['ln_Opening_Weekend_Gross']

model1 = sm.OLS(y, X1).fit()

print(model1.summary())

X2 = reg_df[['Tomatometer',
            'ln_Number_of_Reviews']]

X2 = sm.add_constant(X2)

model2 = sm.OLS(y, X2).fit()

print(model2.summary())

X3 = reg_df[['Tomatometer',
            'ln_Number_of_Reviews',
            'Franchise_Status',
            'ln_Budget',
            'Year']]

X3 = sm.add_constant(X3)

model3 = sm.OLS(y, X3).fit(cov_type='HC3')

print(reg_df.describe())
print(model3.summary())

from statsmodels.stats.outliers_influence import variance_inflation_factor
X_vif = reg_df[['Tomatometer',
                'ln_Number_of_Reviews',
                'Franchise_Status',
                'ln_Budget',
                'Year']]

vif = pd.DataFrame()
vif['Variable'] = X_vif.columns

vif['VIF'] = [
    variance_inflation_factor(X_vif.values, i)
    for i in range(X_vif.shape[1])
]

print(vif)

print("Model 1 Adj R²:", model1.rsquared_adj)
print("Model 2 Adj R²:", model2.rsquared_adj)
print("Model 3 Adj R²:", model3.rsquared_adj)
print("Number of observations:", len(reg_df))