"""canvod-filemap: naming recipes for non-canonical GNSS filenames."""

__version__ = "0.1.0"

from .convention import (
    AgencyId,
    CanVODFilename,
    ContentCode,
    Duration,
    FileType,
    ReceiverType,
    SiteId,
)
from .mapping import VirtualFile
from .recipe import NamingRecipe
from .recipe_files import RecipeNotFoundError, create_recipe, find_recipe, recipe_path

__all__ = [
    "AgencyId",
    "CanVODFilename",
    "ContentCode",
    "Duration",
    "FileType",
    "NamingRecipe",
    "ReceiverType",
    "RecipeNotFoundError",
    "SiteId",
    "VirtualFile",
    "create_recipe",
    "find_recipe",
    "recipe_path",
]
