"""canvod-filemap: naming recipes for non-canonical GNSS filenames."""

__version__ = "0.1.0"

from .mapping import VirtualFile
from .recipe import NamingRecipe
from .recipe_files import RecipeNotFoundError, create_recipe, find_recipe, recipe_path

__all__ = [
    "NamingRecipe",
    "RecipeNotFoundError",
    "VirtualFile",
    "create_recipe",
    "find_recipe",
    "recipe_path",
]
