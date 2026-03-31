import numpy as np
import matplotlib.pyplot as plt

np.random.seed(2)

minutes = np.random.normal(3, 1, 100)
print(f'minutes = {minutes}')
money_spent = np.random.normal(150, 40, 100) / minutes
print(f'money_spent = {money_spent}')

plt.scatter(minutes, money_spent)
plt.show()

train_minutes = minutes[:80]
train_money_spent = money_spent[:80]

test_minutes = minutes[80:]
test_money_spent = money_spent[80:]

plt.scatter(train_minutes, train_money_spent)
plt.show()

plt.scatter(test_minutes, test_money_spent)
plt.show()

mymodel = np.poly1d(np.polyfit(train_minutes, train_money_spent, 4))
myline = np.linspace(0, 6, 100)

plt.scatter(train_minutes, train_money_spent)
plt.plot(myline, mymodel(myline))
plt.show()

#we would like to measure the relationship between the minutes a customer stays in the shop and how much money they spend
from sklearn.metrics import r2_score
r2 = r2_score(train_money_spent, mymodel(train_minutes))
print(f'r2 = {r2}')

#find the R2 score when using testing data:
r2_ = r2_score(test_money_spent, mymodel(test_minutes))
print(f'r2_ = {r2_}')

#How much money will a buying customer spend, if she or he stays in the shop for 5 minutes?
print('mymodel(5) = ', mymodel(5))