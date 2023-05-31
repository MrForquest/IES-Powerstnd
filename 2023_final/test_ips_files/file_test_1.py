import numpy as np


def sun_formule(x, y):
    f0 = np.array([1] * len(x))
    f1 = np.array(x)
    Y = np.array([[dy] for dy in y])
    w = np.array([np.nan, np.nan])
    X = np.array([f0, f1]).T
    coef_matrix = np.dot(np.dot(np.linalg.inv(np.dot(X.T, X)), X.T), Y)

    b = coef_matrix.T[0][0]
    coef = coef_matrix.T[0][1]
    # print(coef_matrix)
    # рассчитаем коэффициенты используя формулу
    return coef, b


print(sun_formule([1, 2, 3, 4], [4, 7, 8, 10]))


class POPA(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pol = 132


pol = list()
pol.append(12)
pol = POPA(pol)
print(pol)
print(pol.pol)

