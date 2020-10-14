"""
common plotting utilities, etc.
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from ruamel.yaml import YAML

yaml = YAML(typ="safe")

with open("cfg.yaml") as f:
    config = yaml.load(f)
    
    
dest_dir = Path("~/Documents/Jupyter/pres/2020/jupytercon").expanduser()


def savefig(name, **savefig_params):
    dest = dest_dir.joinpath(name + ".pdf")
    if not dest_dir.exists():
        # skip savefig e.g.
        return
    #     savefig_params.setdefault("bbox_inches", "tight")
    plt.savefig(dest, **savefig_params)
    print(f"Saved {dest}")


def interpolate_one(ts, target):
    # https://stackoverflow.com/questions/18182030
    # Thanks Dan!

    target = pd.to_datetime(target, utc=True)
    if target in ts.index:
        return ts[target]
    ts1 = ts.sort_index()
    b = (ts1.index > target).argmax()  # index of first entry after target
    s = ts1.iloc[b - 1 : b + 1]

    # Insert empty value at target time.
    return s.resample("1d").interpolate(method="time").loc[target]


def add_lines(sample, lines=None, alternate=True):
    """Add some significant dates as annotations to a line plot"""
    if lines is None:
        lines = config["dates"]
    ax = plt.gca()
    # date, text = "2010-05-10", "ipython on github"
    for i, (date, text) in enumerate(lines.items()):

        if i % 2 == 0 or not alternate:
            xy = (-64, 100)
            align = "right"
        else:
            xy = (64, -80)
            align = "left"

        ax.annotate(
            text,
            xy=(date, interpolate_one(sample, date)),
            xycoords="data",
            xytext=xy,
            textcoords="offset points",
            arrowprops=dict(facecolor="black", shrink=0.05),
            horizontalalignment=align,
        )


def plot_events(
    df,
    events=None,
    org=None,
    since=None,
    year=None,
    n=5,
    freq="M",
    groupby="repo_name",
    column="actor_id",
    metric="count",
    timeseries=False,
    smooth=None,
    **plot_args,
):
    """Charts of common events
    
    timeseries or bar chart
    """

    mask = True
    if events:
        if isinstance(events, str):
            events = [events]
        mask &= df.type.isin(events)
    if org:
        if isinstance(org, str):
            org = [org]
        mask &= df.org.isin(org)
    if since:
        mask &= df.date >= since
    if year:
        mask &= df.date.dt.year == year

    if mask is not True:
        df = df[mask]

    if timeseries:
        grouper = [pd.Grouper(freq=freq, key="date")]
        if groupby is not None:
            grouper.append(groupby)
        plot_args.setdefault("kind", "area")
        if plot_args["kind"] == "area":
            plot_args.setdefault("linewidth", 0)
    else:
        grouper = groupby
        plot_args.setdefault("kind", "bar")
    #         data = data.nlargest(n)
    if grouper:
        grouped = df.groupby(grouper)
    data = getattr(getattr(grouped, column), metric)()
    #     if metric == "total":
    #         data = grouped.actor_id.count()
    #     elif metric == "unique":
    #         data = grouped.actor_id.nunique()
    #     else:
    #         raise ValueError(f"metric must be 'total' or 'unique', not {metric!r}")
    #     if plot_args.get("kind") == "bar":
    #         data = data.nlargest(n)
    if timeseries:
        if groupby:
            data = data.unstack(-1)
        if smooth:
            data = data.rolling(smooth).mean()
    else:
        data = data.nlargest(n)

    data.plot(**plot_args)
    if not timeseries:
        plt.grid(False)

    return data
