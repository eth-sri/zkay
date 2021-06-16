import numpy as np
import matplotlib.pyplot as plt


def create(values, style_arg):
    """
    Plots a cumulative distribution function over the nonnegative entries in values.
    """
    nof_points = len(values)
    sorted_val = np.array(sorted([0] + values))
    ys = np.arange(0, nof_points+1) / nof_points
    plt.step(sorted_val, ys, style_arg, where='post')
    plt.xlim([0, sorted_val[-1]])
    plt.ylim([0,1])
    plt.ylabel("CDF")
