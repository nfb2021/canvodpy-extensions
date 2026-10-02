"""canvod-filemap: Filename convention and mapping engine for canVODpy."""

__version__ = "0.1.0"

from .config_models import DirectoryLayout, ReceiverNamingConfig, SiteNamingConfig
from .convention import (
    AgencyId,
    CanVODFilename,
    ContentCode,
    Duration,
    FileType,
    ReceiverType,
    SiteId,
)
from .mapping import FilenameMapper, VirtualFile
from .patterns import BUILTIN_PATTERNS, SourcePattern, match_pattern
from .recipe import NamingRecipe
from .recipe_files import RecipeNotFoundError, create_recipe, find_recipe, recipe_path
from .validator import DataDirectoryValidator, ValidationReport

__all__ = [
    "BUILTIN_PATTERNS",
    "AgencyId",
    "CanVODFilename",
    "ContentCode",
    "DataDirectoryValidator",
    "DirectoryLayout",
    "Duration",
    "FileType",
    "FilenameMapper",
    "NamingRecipe",
    "ReceiverNamingConfig",
    "ReceiverType",
    "RecipeNotFoundError",
    "SiteId",
    "SiteNamingConfig",
    "SourcePattern",
    "ValidationReport",
    "VirtualFile",
    "create_recipe",
    "find_recipe",
    "match_pattern",
    "recipe_path",
]
