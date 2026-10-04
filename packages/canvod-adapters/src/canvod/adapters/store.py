"""VOD store I/O through any :class:`~canvod.adapters.base.VodAdapter`.

Requires the ``store`` extra (``canvod-adapters[store]``).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from canvod.utils.tools import file_hash

if TYPE_CHECKING:
    from canvod.adapters.base import VodAdapter
    from canvod.store import MyIcechunkStore


def import_vod(
    adapter: VodAdapter,
    path: Path | str,
    store: MyIcechunkStore,
    analysis_name: str,
    *,
    branch: str = "main",
    dedup: bool = True,
) -> bool:
    """Import one of a tool's VOD files into a canvodpy VOD store.

    The data goes to the group ``{tool}/{analysis_name}``: the tool takes
    the place of the VOD model, so imported VOD stays apart from VOD that
    canvodpy computed.

    Parameters
    ----------
    adapter : VodAdapter
        Adapter of the tool that wrote the file.
    path : Path or str
        The tool's VOD file.
    store : MyIcechunkStore
        Destination VOD store (e.g. ``site.vod_store``).
    analysis_name : str
        Analysis the VOD belongs to (e.g. ``"canopy_01_vs_reference_01"``).
    branch : str, default "main"
        Icechunk branch to write to.
    dedup : bool, default True
        Skip the write if this file was already imported, or if its epochs
        overlap data already in the group.

    Returns
    -------
    bool
        ``True`` if written, ``False`` if skipped as a duplicate.

    Raises
    ------
    ValueError
        If the converted data does not meet the VOD dataset contract.
    """
    path = Path(path)
    ds = adapter.import_file(path)
    tool = adapter.tool.name
    return store.write_or_append_vod_group(
        ds,
        f"{tool}/{analysis_name}",
        source_file_hashes={tool: file_hash(path)},
        source_gnss_stores={tool: str(path)},
        calculator_name=tool,
        branch=branch,
        commit_message=f"Imported {tool} VOD from {path.name}",
        dedup=dedup,
    )


def export_vod(
    adapter: VodAdapter,
    store: MyIcechunkStore,
    group_name: str,
    path: Path | str,
    *,
    branch: str = "main",
) -> Path:
    """Export a VOD store group as one of a tool's VOD files.

    Parameters
    ----------
    adapter : VodAdapter
        Adapter of the tool to write for.
    store : MyIcechunkStore
        Source VOD store (e.g. ``site.vod_store``).
    group_name : str
        VOD group, ``{model}/{analysis_name}`` (e.g.
        ``"tau_omega_zeroth_order/canopy_01_vs_reference_01"``).
    path : Path or str
        File to write.
    branch : str, default "main"
        Icechunk branch to read from.

    Returns
    -------
    Path
        ``path``.
    """
    vod_ds = store.read_group(group_name, branch=branch).load()
    return adapter.export_file(vod_ds, path, source=group_name)
