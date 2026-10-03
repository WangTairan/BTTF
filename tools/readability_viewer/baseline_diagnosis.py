"""Replay baseline feature contributions from recorded inputs and fixed models."""
from __future__ import annotations

import json
import math
from functools import lru_cache

from .diagnosis import ROOT
from src.methods.dorn.method import stable_sigmoid


DORN_LABELS = {
    'Dorn-Visual-X-Identifiers': ('Identifier layout (horizontal)', 'How rapidly the visual pattern of identifier characters changes from left to right. It measures spatial frequency, not the meaning of the names.'),
    'Dorn-Visual-X-Comments': ('Comment layout (horizontal)', 'How rapidly the visual pattern of comment characters changes from left to right.'),
    'Dorn-DFT-Comments': ('Comment layout frequency', 'How frequently the layout switches between lines containing only comments or whitespace and lines containing code.'),
    'Dorn-DFT-Numbers': ('Number layout frequency', 'How rapidly the number of numeric values per line changes through the code.'),
    'Dorn-DFT-Indentations': ('Indentation frequency', 'How rapidly indentation changes from line to line.'),
    'Dorn-Areas-Operators': ('Operator visual area', 'The share of the code’s visual area occupied by operators such as +, =, and *.'),
    'Dorn-Visual-Y-Identifiers': ('Identifier layout (vertical)', 'How rapidly the visual pattern of identifier characters changes from top to bottom.'),
}


@lru_cache(maxsize=1)
def dorn_parameters():
    return json.loads((ROOT / 'frozen_models/dorn_retrained/model.json').read_text())


def decompose_baseline(method, detail):
    if method == 'posnett':
        intercept = 8.87
        features = [
            {'key': key, 'name': name, 'description': description,
             'value': float(detail[key]), 'contribution': coefficient * float(detail[key])}
            for key, name, description, coefficient in [
                ('lines', 'Source lines', 'The number of non-empty source lines.', .40),
                ('halstead_volume', 'Halstead volume', 'How much symbolic information the code contains. It combines the total number of operators and values with the number of distinct ones.', -.033),
                ('byte_entropy', 'Byte entropy', 'How varied the bytes in the source text are. Repeated bytes give a lower value; a more even mixture gives a higher value.', -1.5),
            ]
        ]
    elif method == 'dorn_retrained':
        model = dorn_parameters()
        intercept = float(model['intercept'])
        features = []
        for key, median, mean, scale, coefficient in zip(
            model['selected_features'], model['imputation_medians'],
            model['standardization_means'], model['standardization_scales'], model['coefficients'],
        ):
            raw = detail['raw_features'][key]
            value = float(raw) if raw is not None and math.isfinite(float(raw)) else float(median)
            name, description = DORN_LABELS[key]
            features.append({'key': key, 'name': name, 'description': description,
                             'value': value, 'contribution': coefficient * (value - mean) / scale})
    else:
        raise ValueError('No baseline decomposition is available for this method')
    logit = intercept + sum(feature['contribution'] for feature in features)
    score = stable_sigmoid(logit)
    if not math.isclose(score, float(detail['score']), rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError('Baseline decomposition does not reconstruct the recorded score')
    if method == 'posnett' and not math.isclose(logit, float(detail['z_value']), abs_tol=1e-9):
        raise ValueError('Posnett decomposition does not reconstruct the recorded log-odds')
    return {'intercept': intercept, 'logit': logit, 'score': score,
            'features': sorted(features, key=lambda feature: abs(feature['contribution']), reverse=True)}
