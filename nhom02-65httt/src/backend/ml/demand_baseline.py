import numpy as np
from sklearn.linear_model import LinearRegression


class DemandBaseline:
    def __init__(self):
        self.model = LinearRegression()

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)


if __name__ == "__main__":
    X = np.array([[1], [2], [3], [4], [5]], dtype=float)
    y = np.array([2, 4, 6, 8, 10], dtype=float)
    model = DemandBaseline().fit(X, y)
    print("Du bao x=6:", model.predict(np.array([[6]])))
