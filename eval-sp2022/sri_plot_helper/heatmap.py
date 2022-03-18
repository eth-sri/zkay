import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def create(data, row_ticks, col_ticks, ax=None,
            cbar_kw={}, cbarlabel="", cbarpos=(0.95, 0.9), row_label=None, row_label_pos=(-0.083, 1.02), col_label=None, col_label_pos=None, reverse=True, **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.
    Follows: https://matplotlib.org/gallery/images_contours_and_fields/image_annotated_heatmap.html

    Parameters
    ----------
    data
        A 2D numpy array of shape (N, M).
    row_ticks
        A list or array of length N with the labels for the rows.
    col_ticks
        A list or array of length M with the labels for the columns.
    ax
        A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
        not provided, use current axes or create a new one.  Optional.
    cbar_kw
        A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    cbarlabel
        The label for the colorbar.  Optional.
    cbarpos
        Position of the colorbar.  Optional.
    row_label
        Label for rows.  Optional.
    col_label
        Label for columns.  Optional.
    row_label_pos
        Position of row label
    col_label_pos
        Position of col label
    reverse
        If true, reverse rows (displaying bottom-up instead of top-down).
        Optional. Default: true
    **kwargs
        All other arguments are forwarded to `imshow`.
    """

    if not ax:
        ax = plt.gca()

    if reverse:
        data = np.flip(data, axis=0)
        row_ticks = reversed(row_ticks)

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    # cax = ax.figure.add_axes([ax.get_position().x1,ax.get_position().y0,0.02,ax.get_position().height])
    cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
    cbar.outline.set_linewidth(0)
    cbar.ax.set_ylabel(cbarlabel, rotation=0, va="baseline")
    cbar.ax.yaxis.set_label_coords(*cbarpos)

    # We want to show all ticks...
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    # ... and label them with the respective list entries.
    ax.set_xticklabels(col_ticks)
    ax.set_yticklabels(row_ticks)

    # Let the horizontal axes labeling appear on bottom.
    ax.tick_params(top=False, bottom=True,
                   labeltop=False, labelbottom=True)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=0)
    # ha="right", rotation_mode="anchor"
    
    # add labels
    if col_label:
        plt.xlabel(col_label)
        if col_label_pos is not None:
            ax.xaxis.set_label_coords(*col_label_pos)
    if row_label:
        plt.ylabel(row_label, rotation=0, horizontalalignment='left')
        ax.yaxis.set_label_coords(*row_label_pos)

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)

    return im, cbar


def annotate(im, data=None, valfmt="{x:.2f}",
                     textcolors=["black", "white"],
                     threshold=None, **textkw):
    """
    A function to annotate a heatmap.

    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A list or array of two color specifications.  The first is used for
        values below a threshold, the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """

    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)

    return texts
