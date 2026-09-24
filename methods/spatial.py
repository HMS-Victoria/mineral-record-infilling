"""Protocol 29: finite-window, untruncated, area-normalized spatial arrays.

These functions contain no fitting, model loading, labels or absolute coordinates.
"""
from functools import lru_cache
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.special import logsumexp

BANDWIDTHS = (2, 5, 10, 20)
MINERALS = ('Gold', 'Silver', 'Zinc', 'Lead', 'Copper', 'Nickel', 'Iron',
            'Uranium', 'Tungsten', 'Manganese')
FEATURE_NAMES = tuple(name for mineral in MINERALS for name in
    (f'{mineral}:log1p_distance_clipped142', f'{mineral}:exists',
     *(f'{mineral}:log1p_D_h{h}' for h in BANDWIDTHS))) + tuple(
         f'E_h{h}' for h in BANDWIDTHS)


@lru_cache(maxsize=4)
def _kernel(h):
    delta = 2.0 * (np.arange(50)[:, None] - np.arange(50)[None, :])
    out = np.exp(-delta * delta / (2.0 * h * h))
    out.setflags(write=False)
    return out


def _log_convolve(planes, h):
    """Fast separable sums; direct log-sum-exp rescues extreme-distance tails.

    A Gaussian in two dimensions factorizes exactly. Products smaller than
    float64 can represent are never used to decide whether context exists.
    For a tiny convolution, recompute its log from all nonzero source cells;
    no kernel radius or source point is truncated. Chunking bounds memory.
    """
    kernel = _kernel(h)
    sums = kernel @ planes @ kernel.T
    with np.errstate(divide='ignore'):
        logs = np.log(sums)
    for i, plane in enumerate(planes):
        source = np.argwhere(plane > 0)
        if not len(source):
            continue
        targets = np.argwhere(sums[i] < 1e-200)
        weights = np.log(plane[source[:, 0], source[:, 1]])
        for start in range(0, len(targets), 128):
            xy = targets[start:start + 128]
            d2 = np.square(xy[:, None, :] - source[None, :, :]).sum(axis=2) * 4.0
            logs[i, xy[:, 0], xy[:, 1]] = logsumexp(
                weights[None, :] - d2 / (2.0 * h * h), axis=1)
    return logs


def densities(tile, context):
    """Return D[bandwidth,mineral,row,col], E[bandwidth,row,col], float64."""
    visible = np.asarray(context['visible'], dtype=np.float64)
    available = np.asarray(context['availability'], dtype=bool)
    valid = np.asarray(tile['valid'], dtype=bool)
    area = np.asarray(tile['area_km2'], dtype=np.float64)
    assert visible.shape == (10, 50, 50)
    assert available.shape == valid.shape == area.shape == (50, 50)
    assert np.isin(visible, (0, 1)).all() and not (available & ~valid).any()
    assert not visible[:, ~available].any()
    assert np.isfinite(area).all() and (area >= 0).all() and (area[valid] > 0).all()
    d = np.zeros((4, 10, 50, 50), dtype=np.float64)
    e = np.zeros((4, 50, 50), dtype=np.float64)
    if not available.any():
        return d, e
    planes = np.concatenate((visible, (area * available)[None], (area * valid)[None]))
    for k, h in enumerate(BANDWIDTHS):
        logs = _log_convolve(planes, h)
        d[k] = np.exp(logs[:10] - logs[10])
        e[k] = np.exp(logs[10] - logs[11])
    assert np.isfinite(d).all() and np.isfinite(e).all()
    assert (e >= 0).all() and (e <= 1 + 2e-14).all()
    return d, e


def features(tile, context, density_arrays=None):
    """64 fixed features, shape [row,col,feature], float64.

    Optional already-computed densities avoid repeating identical array work
    when a caller also needs KDE scores; callers must use the same context.
    """
    d, e = densities(tile, context) if density_arrays is None else density_arrays
    visible = np.asarray(context['visible'], dtype=bool)
    out = np.empty((50, 50, 64), dtype=np.float64)
    for c, mask in enumerate(visible):
        exists = mask.any()
        distance = distance_transform_edt(~mask, sampling=2.0) if exists else np.full((50, 50), 142.0)
        out[:, :, 6*c] = np.log1p(np.minimum(distance, 142.0))
        out[:, :, 6*c + 1] = exists
        out[:, :, 6*c + 2:6*c + 6] = np.log1p(d[:, c]).transpose(1, 2, 0)
    out[:, :, 60:64] = e.transpose(1, 2, 0)
    assert np.isfinite(out).all()
    return out
