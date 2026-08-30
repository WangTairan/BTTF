"""PyTorch reconstruction of the published ConvNetCR architecture."""

from __future__ import annotations

import os

# This repository's supported transformer stack already requires this on the
# macOS Conda environment because PyTorch and scientific Python load separate
# OpenMP runtimes.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import torch
from torch import nn


class MiConvNetCR(nn.Module):
    """Character-level branch from Mi et al. (IST 2018).

    The paper selects three filter banks of height 2, each spanning the complete
    line width, with 100 feature maps per bank. Global max pooling converts each
    bank to a fixed vector before the two-way classifier.
    """

    def __init__(
        self,
        *,
        line_width: int,
        filter_heights: tuple[int, ...] = (2, 2, 2),
        feature_maps: int = 100,
        dropout: float = 0.5,
    ) -> None:
        super().__init__()
        if line_width < 1:
            raise ValueError("line_width must be positive")
        if not filter_heights:
            raise ValueError("At least one filter height is required")
        self.line_width = int(line_width)
        self.filter_heights = tuple(int(value) for value in filter_heights)
        self.feature_maps = int(feature_maps)
        self.convolutions = nn.ModuleList(
            nn.Conv2d(1, self.feature_maps, (height, self.line_width))
            for height in self.filter_heights
        )
        self.dropout = nn.Dropout(float(dropout))
        self.classifier = nn.Linear(
            self.feature_maps * len(self.filter_heights),
            2,
        )

    def forward(self, matrix: torch.Tensor) -> torch.Tensor:
        if matrix.ndim != 3:
            raise ValueError(
                f"Expected [batch, lines, width], received {tuple(matrix.shape)}"
            )
        if matrix.shape[-1] != self.line_width:
            raise ValueError(
                f"Expected line width {self.line_width}, received {matrix.shape[-1]}"
            )
        image = matrix.unsqueeze(1)
        pooled = []
        for convolution in self.convolutions:
            feature_map = torch.relu(convolution(image)).squeeze(-1)
            pooled.append(torch.amax(feature_map, dim=-1))
        features = self.dropout(torch.cat(pooled, dim=1))
        return self.classifier(features)
