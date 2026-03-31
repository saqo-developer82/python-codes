import pandas

df = pandas.read_csv('data/Persons.csv')
print(df)

d = {'UK': 0, 'USA': 1, 'N': 2}
df['Nationality'] = df['Nationality'].map(d)
d = {'YES': 1, 'NO': 0}
df['Go'] = df['Go'].map(d)

print(df)

##Separate the feature columns from the target column. The feature columns are the columns that we try to predict from, and the target column is the column with the values we try to predict.

#X is the feature columns, y is the target column:
features = ['Age', 'Experience', 'Rank', 'Nationality']

X = df[features]
y = df['Go']

print(f'X = \n{X}')
print(f'y = \n{y}')

#Create the actual decision tree, fit it with our details.
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt

dtree = DecisionTreeClassifier()
dtree = dtree.fit(X, y)

tree.plot_tree(dtree, feature_names=features)

#Should I go see a show starring a 40 years old American comedian, with 10 years of experience, and a comedy ranking of 7?
print(dtree.predict([[40, 10, 7, 1]]))