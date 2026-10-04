"""Provenance of a conversion between canvodpy and another tool."""

from __future__ import annotations

from datetime import UTC, datetime
from importlib import metadata as importlib_metadata
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

#: Prefix of the provenance attributes on a converted dataset.
ATTR_PREFIX = "conversion_"

#: Recorded as the version of a package that is not installed.
NOT_INSTALLED = "not installed"


class Tool(BaseModel):
    """A program canvodpy exchanges data with.

    Parameters
    ----------
    name : str
        Short name, also the model layer of imported VOD in the VOD store
        (e.g. ``"gnssvod"``).
    distribution : str
        Name of its installed Python distribution, to record its version.
    url : str
        Where to find it.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    distribution: str
    url: str


def package_version(distribution: str) -> str:
    """Installed version of ``distribution``, or :data:`NOT_INSTALLED`.

    A conversion need not have the other tool installed (e.g. importing a
    gnssvod NetCDF file), so a missing package is recorded, not an error.
    """
    try:
        return importlib_metadata.version(distribution)
    except importlib_metadata.PackageNotFoundError:
        return NOT_INSTALLED


class Provenance(BaseModel):
    """Which tool data was converted from or to, by what, when.

    Parameters
    ----------
    tool : str
        Name of the other tool.
    tool_url : str
        Where to find it.
    tool_version : str
        Its installed version at conversion time, or :data:`NOT_INSTALLED`.
    adapter_version : str
        Version of canvod-adapters.
    direction : {"import", "export"}
        ``"import"``: from the tool into canvodpy; ``"export"``: the reverse.
    source : str
        What was converted, e.g. a file name or a VOD store group.
    created : datetime
        When (UTC).
    """

    model_config = ConfigDict(frozen=True)

    tool: str
    tool_url: str
    tool_version: str
    adapter_version: str
    direction: Literal["import", "export"]
    source: str
    created: datetime

    @classmethod
    def now(cls, tool: Tool, direction: Literal["import", "export"], source: str) -> Provenance:
        """Provenance of a conversion running now, with installed versions."""
        return cls(
            tool=tool.name,
            tool_url=tool.url,
            tool_version=package_version(tool.distribution),
            adapter_version=package_version("canvod-adapters"),
            direction=direction,
            source=source,
            created=datetime.now(UTC),
        )

    def to_attrs(self) -> dict[str, str]:
        """Dataset attributes, each name prefixed with :data:`ATTR_PREFIX`."""
        return {
            f"{ATTR_PREFIX}{key}": str(value)
            for key, value in self.model_dump(mode="json").items()
        }

    @classmethod
    def from_attrs(cls, attrs: dict[str, Any]) -> Provenance:
        """Read provenance back from dataset attributes.

        Raises
        ------
        pydantic.ValidationError
            If the attributes hold no complete provenance.
        """
        return cls.model_validate(
            {
                key.removeprefix(ATTR_PREFIX): value
                for key, value in attrs.items()
                if key.startswith(ATTR_PREFIX)
            }
        )
