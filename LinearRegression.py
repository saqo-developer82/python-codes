import pandas as pd
from sklearn import linear_model

df = pd.read_csv("data/CarsList.csv")
print(df)

X = df[['Weight', 'Volume']]
y = df['CO2']

regr = linear_model.LinearRegression()
regr.fit(X, y)

#predict the CO2 emission of a car where the weight is 2300kg, and the volume is 1300cm3:
predictedCO2 = regr.predict([[2300, 1300]])
print(f'predictedCO2 = {predictedCO2}')

#Print the coefficient values of the regression object
print(f'regr.coef_ = {regr.coef_}')

predictedCO2_ = regr.predict([[3300, 1300]])
print(f'predictedCO2_ = {predictedCO2_}')