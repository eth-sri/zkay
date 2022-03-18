import matplotlib.pyplot as plt
import sri_plot_helper.cdf
import sri_plot_helper.heatmap
from matplotlib import rc, rcParams


def configure_plots(font_style: str = 'CM', font_size: int = 12, preamble: str = ''):
    """
    Configure plots. Call this function once before using any other function of this module.

    Args:
        font_style: choice of 'IEEE', 'ACM', 'CM' for different conference paper templates
        font_size: the size of the text
        preamble: additional latex definitions and packages
    """
    # enable latex
    rc('text', usetex=True)

    # set correct font encoding (T1)
    rcParams['pdf.fonttype'] = 42
    rcParams['ps.fonttype'] = 42

    if font_style == "IEEE":
        # setup IEEE times font
        rc('font', **{'family': 'serif', 'serif': ['Times'], 'size': font_size})
        plt.rc('text.latex', preamble=preamble)
    elif font_style == "ACM":
        # setup ACM Linux Libertine font
        rc('font', **{'family': 'serif', 'size': font_size})
        rc('text.latex', preamble=r"\usepackage{libertine}\usepackage[libertine]{newtxmath}\n" + preamble)
    elif font_style == "CM":
        # use standard Computer Modern serif font
        rc('font', **{'family': 'serif', 'size': font_size})
        plt.rc('text.latex', preamble=preamble)
    else:
        raise Exception('font_style "{}" unknown'.format(font_style))

    # configure nice legend
    rc('legend', fancybox=False)  # disable rounded corners
    rc('legend', frameon=False)  # disable background


def subplots(
        *args,
        in_cm=True,
        top_spine=False,
        right_spine=False,
        bottom_spine=False,
        left_spine=False,
        nice_grid='y',
        **kwargs):
    """
    Create a figure and a set of subplots.

    Args:
        *args: additional arguments for pyplot
        in_cm: whether the parameter figsize is provided in cm
        top_spine: whether to show the top spine
        right_spine: whether to show the right spine
        bottom_spine: whether to shop the bottom spine
        left_spine: whether to show the left spine
        nice_grid: gray background and white major grid
        **kwargs:
    """
    # potentially transform from cm to inches
    if in_cm:
        if 'figsize' in kwargs:
            # convert cm to inches
            kwargs['figsize'] = (
                kwargs['figsize'][0] * 0.393701,
                kwargs['figsize'][1] * 0.393701
            )

    # generate subplots
    fig, axes = plt.subplots(*args, **kwargs)
    # customize all returned axes
    if hasattr(axes, '__len__'):
        axes_iterable = axes
    else:
        axes_iterable = [axes]

    for ax in axes_iterable:
        # disable box, only keep x and y axis
        ax.spines['top'].set_visible(top_spine)
        ax.spines['right'].set_visible(right_spine)
        ax.spines['bottom'].set_visible(bottom_spine)
        ax.spines['left'].set_visible(left_spine)

        if nice_grid is not None:
            # set light gray background
            ax.set_facecolor("#F5F5F5")

            # set white major grid for y axis
            ax.grid(b=True, which='major', axis=nice_grid, color='w')
            ax.set_axisbelow(True)

    return fig, axes


def new_figure(width_cm, height_cm, **kwargs):
    """
    Wrapper for subplots.

    Args:
        width_cm: width of the figure in cm
        height_cm: height of the figure in cm
        **kwargs: additional arguments for pyplot
    """
    return subplots(figsize=(width_cm, height_cm), **kwargs)


def savefig(filename, tight=True, **kwargs):
    """
    Saves the figure to a file.

    Args:
        filename: the filename of the target file (must include file extension)
        tight: whether to use a tight layout
        **kwargs: additional arguments for pyplot
    """
    if tight:
        more_args = {'bbox_inches': 'tight', 'pad_inches': 0}
    plt.savefig(filename, **kwargs, **more_args)


def pdfcrop(inputfile, outputfile, marginleft=0, margintop=0, marginright=0, marginbottom=0):
    """
    Crops a given input pdf file.
    """
    import sh
    pdfcrop = sh.Command('pdfcrop')
    pdfcrop(
        '--margins',
        f'{marginleft} {margintop} {marginright} {marginbottom}',
        inputfile,
        outputfile
    )
