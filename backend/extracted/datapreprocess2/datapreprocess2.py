import pandas as pd
import numpy as np

from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler

from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score

from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_selection import RFE

from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Lasso

from sklearn.ensemble import RandomForestRegressor

# =====================================================
# DATASET
# =====================================================

data = {
    'Area':[1000,1200,1500,1800,2000,2200,2500,2700,3000,3500],
    'Bedrooms':[2,2,3,3,4,4,4,5,5,6],
    'Age':[15,12,10,8,7,5,4,3,2,1],
    'Distance':[10,8,7,6,5,4,3,2,2,1],
    'Constant_Feature':[1,1,1,1,1,1,1,1,1,1],
    'Price':[150,180,250,300,350,400,450,500,550,650]
}

df = pd.DataFrame(data)

print("Original Dataset")
print(df)

# =====================================================
# FEATURES AND TARGET
# =====================================================

X = df.drop('Price', axis=1)
y = df['Price']

# =====================================================
# MIN MAX SCALING
# =====================================================

print("\nMIN MAX SCALING")

minmax = MinMaxScaler()

X_minmax = minmax.fit_transform(X)

print(pd.DataFrame(X_minmax,
                   columns=X.columns))

# =====================================================
# STANDARD SCALING
# =====================================================

print("\nSTANDARD SCALING")

standard = StandardScaler()

X_standard = standard.fit_transform(X)

print(pd.DataFrame(X_standard,
                   columns=X.columns))

# =====================================================
# ROBUST SCALING
# =====================================================

print("\nROBUST SCALING")

robust = RobustScaler()

X_robust = robust.fit_transform(X)

print(pd.DataFrame(X_robust,
                   columns=X.columns))

# =====================================================
# TRAIN TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print("\nTrain Size:", len(X_train))
print("Test Size:", len(X_test))

# =====================================================
# TRAIN VALIDATION TEST SPLIT
# =====================================================

X_train, X_temp, y_train, y_temp = train_test_split(
    X,
    y,
    test_size=0.4,
    random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.5,
    random_state=42
)

print("\nTrain:", len(X_train))
print("Validation:", len(X_val))
print("Test:", len(X_test))

# =====================================================
# STRATIFIED SPLITTING
# =====================================================

df['Category'] = [
    0,0,0,0,1,
    1,1,1,1,1
]

X_strat = df.drop(['Price','Category'], axis=1)
y_strat = df['Category']

X_train, X_test, y_train, y_test = train_test_split(
    X_strat,
    y_strat,
    test_size=0.3,
    stratify=y_strat,
    random_state=42
)

print("\nStratified Split")
print(y_train.value_counts())

# =====================================================
# K FOLD CROSS VALIDATION
# =====================================================

model = LinearRegression()

kfold = KFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

scores = cross_val_score(
    model,
    X,
    y,
    cv=kfold
)

print("\nK Fold Scores")
print(scores)

print("Average:", scores.mean())

# =====================================================
# STRATIFIED K FOLD
# =====================================================

skf = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

scores = cross_val_score(
    LinearRegression(),
    X_strat,
    y_strat,
    cv=skf
)

print("\nStratified K Fold Scores")
print(scores)

# =====================================================
# FILTER METHOD
# CORRELATION MATRIX
# =====================================================

print("\nCorrelation Matrix")

corr = df.corr(numeric_only=True)

print(corr)

# =====================================================
# FILTER METHOD
# VARIANCE THRESHOLD
# =====================================================

selector = VarianceThreshold(
    threshold=0.0
)

X_var = selector.fit_transform(X)

print("\nVariance Threshold")
print("Before:", X.shape[1])
print("After:", X_var.shape[1])

# =====================================================
# WRAPPER METHOD
# RFE
# =====================================================

model = LinearRegression()

rfe = RFE(
    estimator=model,
    n_features_to_select=3
)

rfe.fit(X, y)

print("\nRFE Selected Features")

for feature, selected in zip(
        X.columns,
        rfe.support_):
    print(feature, selected)

# =====================================================
# EMBEDDED METHOD
# LASSO
# =====================================================

lasso = Lasso(alpha=1)

lasso.fit(X, y)

print("\nLasso Coefficients")

for feature, coef in zip(
        X.columns,
        lasso.coef_):
    print(feature, coef)

# =====================================================
# EMBEDDED METHOD
# TREE FEATURE IMPORTANCE
# =====================================================

rf = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

rf.fit(X, y)

print("\nTree Feature Importance")

for feature, importance in zip(
        X.columns,
        rf.feature_importances_):
    print(feature,
          round(importance,4))