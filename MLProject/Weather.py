import pandas as pd

weather = pd.read_csv('../data/local_weather.csv', index_col="DATE")
print(weather)