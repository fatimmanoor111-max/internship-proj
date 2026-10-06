"""Matplotlib / Seaborn (static PNG) and Plotly (interactive HTML) figures."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.inspection import permutation_importance
from sklearn.metrics import ConfusionMatrixDisplay
from config import FIG_DIR

sns.set_theme(style="whitegrid", palette="deep")


def _save(name):
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=140)
    plt.close()


def plot_model_comparison(res, metric, title, fname):
    plt.figure(figsize=(6, 3.5))
    ax = sns.barplot(data=res, x="model", y=metric, hue="model", legend=False)
    for c in ax.containers:
        ax.bar_label(c, fmt="%.3f")
    plt.title(title); plt.xlabel("")
    _save(fname)


def plot_confusion(y_true, y_pred, title, fname):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=["On time", "Delayed 15+"],
                                            cmap="Blues", ax=ax, colorbar=False)
    ax.set_title(title); ax.grid(False)
    _save(fname)


def plot_importance(pipe, X, y, title, fname, scoring="f1"):
    r = permutation_importance(pipe, X, y, n_repeats=5, random_state=42, scoring=scoring, n_jobs=-1)
    imp = sorted(zip(X.columns, r.importances_mean), key=lambda t: t[1])
    plt.figure(figsize=(6, 4))
    plt.barh([a for a, _ in imp], [b for _, b in imp], color=sns.color_palette("deep")[0])
    plt.title(title); plt.xlabel(f"Drop in {scoring} when shuffled")
    _save(fname)


def plot_pred_vs_actual(y, pred, title, fname):
    plt.figure(figsize=(5, 4.5))
    sns.scatterplot(x=y, y=pred, alpha=.35, s=14)
    lim = [min(y.min(), pred.min()), max(y.max(), pred.max())]
    plt.plot(lim, lim, "r--", lw=1)
    plt.xlabel("Actual"); plt.ylabel("Predicted"); plt.title(title)
    _save(fname)


def plot_forecast(dates, actual, pred, naive):
    plt.figure(figsize=(8, 3.8))
    plt.plot(dates, actual, "o-", label="Actual")
    plt.plot(dates, pred, "s--", label="GradientBoosting")
    plt.plot(dates, naive, ":", label="Seasonal naive (t-7)", alpha=.7)
    plt.title("Daily passengers - 14-day hold-out forecast"); plt.legend(); plt.xticks(rotation=30)
    _save("07_forecast.png")


def plot_clusters(rf, Z):
    from sklearn.decomposition import PCA
    p = PCA(2, random_state=42).fit_transform(Z)
    rf = rf.assign(pc1=p[:, 0], pc2=p[:, 1], cluster=rf.cluster.astype(str))
    plt.figure(figsize=(7, 4.5))
    sns.scatterplot(data=rf, x="pc1", y="pc2", hue="cluster", s=120)
    for _, r in rf.iterrows():
        plt.annotate(r.route_name.split(" - ")[0], (r.pc1, r.pc2), xytext=(5, 5), textcoords="offset points", fontsize=8)
    plt.title("Route segments (KMeans on PCA projection)")
    _save("08_route_clusters.png")
    px.scatter(rf, x="pc1", y="pc2", color="cluster", hover_name="route_name", size="avg_pax",
               title="Route segments (interactive)").write_html(FIG_DIR / "08_route_clusters.html")


def plot_anomalies(comp):
    plt.figure(figsize=(6.5, 4.5))
    sns.scatterplot(data=comp, x="traffic_index", y="delay_min", hue="anomaly", palette={False: "#9bb", True: "r"},
                    s=14, alpha=.6)
    plt.title("Anomalous trips (IsolationForest)")
    _save("09_anomalies.png")
    px.scatter(comp, x="traffic_index", y="delay_min", color="anomaly", hover_data=["trip_id", "route_name", "passengers"],
               title="Anomalous trips (interactive)").write_html(FIG_DIR / "09_anomalies.html")
