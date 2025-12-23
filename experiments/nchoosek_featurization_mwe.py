import pandas as pd
import numpy as np
import itertools


def dummy_featurizer(candidate):
    """Simple featurizer: sum and sum-of-squares of parameter values."""
    values = list(candidate.values())
    return {"f_sum": sum(values), "f_sqsum": sum(v**2 for v in values)}


def branin_like_from_features(feat):
    """Compute Branin-like objective from features."""
    # use f_sqsum and f_sum as proxies for x1/x2
    x1 = feat["f_sqsum"]
    x2 = feat["f_sum"]
    # scale to Branin-like ranges
    x1s = (x1 / (1.0 + x1)) * 15.0 - 5.0  # map positive -> [-5,10)
    x2s = (x2 / (1.0 + x2)) * 15.0  # map positive -> [0,15)
    # branin-like expression
    a = 1.0
    b = 5.1 / (4 * np.pi**2)
    c = 5.0 / np.pi
    r = 6.0
    s = 10 * (1 - 1.0 / (8 * np.pi))
    y = (x2s - b * x1s**2 + c * x1s - r) ** 2 + s * np.cos(x1s) + 10.0
    return float(y)


def generate_nchoosek_candidates(N=6, K=2, resolution=0.2):
    """Generate all NChooseK candidates at discrete resolution: choose K active params, set to discrete values, others 0.0.

    Returns a DataFrame where columns are x0..x{N-1}, one row per combination of values.
    """
    names = [f"x{i}" for i in range(N)]
    combos = list(itertools.combinations(range(N), K))
    levels = np.arange(0.0, 1.0 + resolution, resolution)
    num_levels = len(levels)
    total_combinations = len(combos) * (num_levels**K)
    print(f"Theoretical number of distinct combinations: {total_combinations}")
    rows = []
    for combo in combos:
        for values in itertools.product(levels, repeat=K):
            row = np.zeros(N, dtype=float)
            for i, idx in enumerate(combo):
                row[idx] = values[i]
            rows.append(row)
    df = pd.DataFrame(rows, columns=names)
    return df


# configure NChooseK problem (small for quick demo)
N = 6
K = 2
resolution = 0.2

candidates = generate_nchoosek_candidates(N=N, K=K, resolution=resolution)

# featurize all candidates
feats = []
for _, row in candidates.iterrows():
    feat = dummy_featurizer(row.to_dict())
    feats.append(feat)
feat_df = pd.DataFrame(feats)

# evaluate objective on features
objectives = feat_df.apply(branin_like_from_features, axis=1)

candidates = candidates.reset_index(drop=True)
candidates["objective"] = objectives
candidates = pd.concat([candidates, feat_df], axis=1)

# find best (lowest) objective
best_idx = candidates["objective"].idxmin()
best_row = candidates.loc[best_idx]

print("Best candidate (first 6 cols are parameters):")
print(best_row.iloc[:N].to_dict())
print("Features:", best_row[["f_sum", "f_sqsum"]].to_dict())
print("Objective:", float(best_row["objective"]))
