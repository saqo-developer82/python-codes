import pandas as pd
from sklearn import linear_model
from sklearn.preprocessing import StandardScaler
scale = StandardScaler()

df = pd.read_csv("data/CarsList1.csv")
print(df)

X = df[['Weight', 'Volume']]
y = df['CO2']

scaledX = scale.fit_transform(X)
print(f'scaledX = \n{scaledX}')

regr = linear_model.LinearRegression()
regr.fit(scaledX, y)

#predict the CO2 emission of a car where the weight is 2300kg, and the volume is 1300cm3:
scaled = scale.transform([[2300, 1.3]])
predictedCO2 = regr.predict([scaled[0]])
print(f'predictedCO2 = {predictedCO2}')