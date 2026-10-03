"""``VirtualFile``: a physical file paired with its canVOD conventional name.

``NamingRecipe.to_virtual_file`` returns it; the file on disk keeps its name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .convention import CanVODFilename


@dataclass(frozen=True)
class VirtualFile:
    """Physical file mapped to its canVOD conventional name."""

    physical_path: Path
    conventional_name: CanVODFilename

    @property
    def canonical_str(self) -> str:
        """The conventional filename as a string."""
        return self.conventional_name.name

    def open(self, mode: str = "rb"):
        """Open the physical file."""
        return self.physical_path.open(mode)
