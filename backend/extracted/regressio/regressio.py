import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score
)
from sklearn.model_selection import train_test_split
data = {
    'Area':[1000,1200,1500,1800,2000,
            2200,2500,2700,3000,3500],

    'Bedrooms':[2,2,3,3,4,
                4,4,5,5,6],

    'Age':[15,12,10,8,7,
           5,4,3,2,1],

    'Price':[150,180,250,300,350,
             400,450,500,550,650]
}

df = pd.DataFrame(data)

print("Dataset")
print(df)



print("\nSIMPLE LINEAR REGRESSION")

X_simple = df[['Area']]
y = df['Price']

simple_model = LinearRegression()

simple_model.fit(X_simple, y)

slope = simple_model.coef_[0]
intercept = simple_model.intercept_

print("Slope =", slope)
print("Intercept =", intercept)

print("\nEquation")

print(f"Price = {intercept:.2f} + ({slope:.4f}) * Area")



print("\nMULTIPLE LINEAR REGRESSION")
X = df[['Area','Bedrooms','Age']]
X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42
)

multi_model = LinearRegression()

multi_model.fit(X_train, y_train)

predictions = multi_model.predict(X_test)

print("Coefficients")

for feature, coef in zip(X.columns,
                         multi_model.coef_):
    print(feature, coef)



mse = mean_squared_error(
    y_test,
    predictions
)

rmse = np.sqrt(mse)

mae = mean_absolute_error(
    y_test,
    predictions
)

r2 = r2_score(
    y_test,
    predictions
)

print("\nMSE =", mse)
print("RMSE =", rmse)
print("MAE =", mae)
print("R2 Score =", r2)

# =====================================================
# GRADIENT DESCENT
# =====================================================

print("\nGRADIENT DESCENT")

x = np.array(df['Area'])
y_actual = np.array(df['Price'])

m = 0
b = 0

learning_rate = 0.00000005

epochs = 1000

n = len(x)

for i in range(epochs):

    y_pred = m*x + b

    dm = (-2/n) * np.sum(
        x * (y_actual-y_pred)
    )

    db = (-2/n) * np.sum(
        y_actual-y_pred
    )

    m = m - learning_rate*dm
    b = b - learning_rate*db

print("Slope:", round(m,4))
print("Intercept:", round(b,4))

# =====================================================
# POLYNOMIAL REGRESSION
# =====================================================

print("\nPOLYNOMIAL REGRESSION")

poly = PolynomialFeatures(
    degree=2
)

X_poly = poly.fit_transform(
    X_simple
)

poly_model = LinearRegression()

poly_model.fit(
    X_poly,
    y
)

poly_pred = poly_model.predict(
    X_poly
)

poly_r2 = r2_score(
    y,
    poly_pred
)

print("Polynomial R2 =", poly_r2)

# =====================================================
# RIDGE REGRESSION (L2)
# =====================================================

print("\nRIDGE REGRESSION")

ridge = Ridge(alpha=1)

ridge.fit(X_train, y_train)

print("Ridge Coefficients")

for feature, coef in zip(
        X.columns,
        ridge.coef_):
    print(feature, coef)

# =====================================================
# LASSO REGRESSION (L1)
# =====================================================

print("\nLASSO REGRESSION")

lasso = Lasso(alpha=1)

lasso.fit(X_train, y_train)

print("Lasso Coefficients")

for feature, coef in zip(
        X.columns,
        lasso.coef_):
    print(feature, coef)

# =====================================================
# ELASTIC NET
# =====================================================

print("\nELASTIC NET")

elastic = ElasticNet(
    alpha=1,
    l1_ratio=0.5
)

elastic.fit(X_train, y_train)

print("ElasticNet Coefficients")

for feature, coef in zip(
        X.columns,
        elastic.coef_):
    print(feature, coef)

# =====================================================
# COMPARISON
# =====================================================

print("\nCOEFFICIENT COMPARISON")

comparison = pd.DataFrame({
    'Feature':X.columns,
    'Linear':multi_model.coef_,
    'Ridge':ridge.coef_,
    'Lasso':lasso.coef_,
    'ElasticNet':elastic.coef_
})

print(comparison)