from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

x = [[2],[4],[6],[8],[1],[3],[5]]
y = [0,1,1,1,0,0,1]    # 0 = Fail, 1 = Pass

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.25, random_state=42
)

model = LinearRegression()
model.fit(x_train, y_train)

result = model.predict(x_test)

print("Actual :", y_test)
print("Predicted :", result)