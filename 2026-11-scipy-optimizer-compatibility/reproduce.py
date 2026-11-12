"""Reproduce the removed iprint keyword failure at SciPy's optimizer boundary."""

import numpy as np
import scipy
from scipy.optimize import fmin_l_bfgs_b


def objective(x):
    return float(np.dot(x, x)), 2 * x


def main():
    print(f"SciPy {scipy.__version__}")

    try:
        fmin_l_bfgs_b(objective, np.array([1.0]), iprint=-1)
    except TypeError as exc:
        if "unexpected keyword argument 'iprint'" not in str(exc):
            raise
        print(f"before: {type(exc).__name__}: {exc}")
    else:
        raise AssertionError("Expected this SciPy version to reject iprint")

    x, value, info = fmin_l_bfgs_b(objective, np.array([1.0]))
    if info["warnflag"] != 0:
        raise AssertionError(f"Optimizer did not converge: {info}")
    print(f"after: converged with x= {x.tolist()} value= {value} warnflag= {info['warnflag']}")


if __name__ == "__main__":
    main()
