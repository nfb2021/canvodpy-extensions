"""Where naming recipe files live, and creating them from the template.

Recipes are kept per site in the configuration directory::

    <config dir>/recipes/<site>/<name>.yaml

``<site>`` is the site name in the settings file and ``<name>`` the
receiver's ``recipe:`` setting. Recipe files are user data: they are not part
of any repository and are only read from this location.
"""

from __future__ import annotations

from pathlib import Path

#: The recipe template shipped with this package.
TEMPLATE_PATH = Path(__file__).parent / "templates" / "recipe.yaml"


class RecipeNotFoundError(FileNotFoundError):
    """No recipe file exists for a site and recipe name."""


def recipe_path(config_dir: Path, site: str, name: str) -> Path:
    """Path of the recipe ``name`` of ``site``, whether it exists or not.

    Parameters
    ----------
    config_dir : Path
        The configuration directory (the one holding the settings file).
    site : str
        Site name in the settings file.
    name : str
        Recipe name, the receiver's ``recipe:`` setting.

    Returns
    -------
    Path
        ``<config_dir>/recipes/<site>/<name>.yaml``.
    """
    return Path(config_dir) / "recipes" / site / f"{name}.yaml"


def find_recipe(config_dir: Path, site: str, name: str) -> Path:
    """Path of the existing recipe file ``name`` of ``site``.

    Parameters
    ----------
    config_dir : Path
        The configuration directory (the one holding the settings file).
    site : str
        Site name in the settings file.
    name : str
        Recipe name, the receiver's ``recipe:`` setting.

    Returns
    -------
    Path
        ``<config_dir>/recipes/<site>/<name>.yaml``.

    Raises
    ------
    RecipeNotFoundError
        If that file does not exist. If the recipe is found directly in
        ``<config_dir>/recipes/``, the message says where to move it.
    """
    path = recipe_path(config_dir, site, name)
    if path.is_file():
        return path
    flat = Path(config_dir) / "recipes" / f"{name}.yaml"
    if flat.is_file():
        msg = (
            f"Recipe '{name}' of site '{site}' must be in a folder named after "
            f"the site. Move {flat} to {path}"
        )
        raise RecipeNotFoundError(msg)
    msg = f"Recipe file not found for '{name}' of site '{site}': {path}"
    raise RecipeNotFoundError(msg)


def create_recipe(config_dir: Path, site: str, name: str, *, overwrite: bool = False) -> Path:
    """Create the recipe ``name`` of ``site`` from the template.

    The new file has ``name`` filled in. The receiver identity and the
    ``fields`` list must be edited before the recipe can be loaded.

    Parameters
    ----------
    config_dir : Path
        The configuration directory (the one holding the settings file).
    site : str
        Site name in the settings file.
    name : str
        Recipe name, the receiver's ``recipe:`` setting.
    overwrite : bool
        Replace an existing recipe file.

    Returns
    -------
    Path
        The created file, ``<config_dir>/recipes/<site>/<name>.yaml``.

    Raises
    ------
    FileExistsError
        If the recipe file exists and ``overwrite`` is false.
    """
    path = recipe_path(config_dir, site, name)
    if path.exists() and not overwrite:
        msg = f"Recipe file already exists: {path}"
        raise FileExistsError(msg)
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    text = text.replace("name: CHANGEME", f"name: {name}", 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
