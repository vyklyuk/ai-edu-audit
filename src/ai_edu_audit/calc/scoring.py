# -*- coding: utf-8 -*-
"""Перетворення значення метрики на бал 0–100, ознака проблеми, підсумок курсу.

Формули перенесено без змін з еталонного build_data.py лінії 1. КОНФІДЕНЦІЙНО.
"""
import math

from . import methodology as M


def score(m, v):
    """Бал 0–100 для значення v метрики m = [code, dim, name, kind, hi, target, accept]."""
    code, dim, name, kind, hi, t, a = m
    if v is None:
        return None
    if hi == "band":
        lo, up = t
        alo, aup = a
        if lo <= v <= up:
            return 100.0
        if v < lo:
            w = lo - alo if lo > alo else max(lo, 0.05)
            return max(0.0, 100 - 60 * (lo - v) / w) if v >= alo - w else 0.0
        w = aup - up if aup > up else 0.05
        return max(0.0, 100 - 60 * (v - up) / w)
    if hi:
        if v >= t:
            return 100.0
        if v >= a:
            return 70 + 30 * (v - a) / (t - a)
        return max(0.0, 70 * v / a) if a else 0.0
    if v <= t:
        return 100.0
    if v <= a:
        return 70 + 30 * (a - v) / (a - t)
    return max(0.0, 70 - 70 * (v - a) / max(a, 1))


def problem(m, v):
    """Чи значення виходить за допуск."""
    hi, a = m[4], m[6]
    if v is None:
        return False
    if hi == "band":
        return not (a[0] <= v <= a[1])
    return v < a if hi else v > a


def total(vals, mdef=None, weights=None):
    """Підсумок курсу: (raw, final, veto, бали вимірів)."""
    mdef = mdef or M.MDEF
    weights = weights or M.WEIGHTS
    dims = {}
    for m in mdef:
        s = score(m, vals.get(m[0]))
        if s is None:
            continue
        dims.setdefault(m[1], []).append(s)
    dsc = {d: math.fsum(v) / len(v) for d, v in dims.items()}
    raw = math.fsum(weights[d] * dsc[d] for d in dsc) / math.fsum(weights[d] for d in dsc)
    veto = any(problem(m, vals.get(m[0])) for m in mdef
               if m[1] in M.VETO_DIMS and vals.get(m[0]) is not None)
    return raw, (min(raw, M.VETO_CAP) if veto else raw), veto, dsc


def pscore(key, name, v):
    """Бал програмної метрики P1–P12."""
    t, a, hi = M.PDEF[key]
    return score([key, "P", name, "", hi, t, a], v)
