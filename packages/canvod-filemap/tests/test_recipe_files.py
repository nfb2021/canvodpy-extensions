"""Tests for the recipe file location and the recipe template."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from canvod.filemap import (
    NamingRecipe,
    RecipeNotFoundError,
    create_recipe,
    find_recipe,
    recipe_path,
)
from canvod.filemap.recipe_files import TEMPLATE_PATH


def test_recipe_path_is_per_site(tmp_path: Path) -> None:
    assert recipe_path(tmp_path, "rosalia", "ref") == (
        tmp_path / "recipes" / "rosalia" / "ref.yaml"
    )


def test_find_recipe_returns_the_site_recipe(tmp_path: Path) -> None:
    path = tmp_path / "recipes" / "rosalia" / "ref.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("name: ref\n")
    assert find_recipe(tmp_path, "rosalia", "ref") == path


def test_find_recipe_of_another_site_is_not_used(tmp_path: Path) -> None:
    other = tmp_path / "recipes" / "other_site" / "ref.yaml"
    other.parent.mkdir(parents=True)
    other.write_text("name: ref\n")
    with pytest.raises(RecipeNotFoundError, match="rosalia"):
        find_recipe(tmp_path, "rosalia", "ref")


def test_missing_recipe_names_the_expected_path(tmp_path: Path) -> None:
    expected = tmp_path / "recipes" / "rosalia" / "ref.yaml"
    with pytest.raises(RecipeNotFoundError, match=str(expected)):
        find_recipe(tmp_path, "rosalia", "ref")


def test_recipe_outside_the_site_folder_says_where_to_move_it(
    tmp_path: Path,
) -> None:
    flat = tmp_path / "recipes" / "ref.yaml"
    flat.parent.mkdir(parents=True)
    flat.write_text("name: ref\n")
    with pytest.raises(RecipeNotFoundError) as excinfo:
        find_recipe(tmp_path, "rosalia", "ref")
    message = str(excinfo.value)
    assert f"Move {flat} to {tmp_path / 'recipes' / 'rosalia' / 'ref.yaml'}" in message


def test_recipe_not_found_is_a_file_not_found_error() -> None:
    assert issubclass(RecipeNotFoundError, FileNotFoundError)


def test_create_recipe_fills_in_the_name(tmp_path: Path) -> None:
    path = create_recipe(tmp_path, "rosalia", "rosalia_reference")
    assert path == tmp_path / "recipes" / "rosalia" / "rosalia_reference.yaml"
    assert yaml.safe_load(path.read_text())["name"] == "rosalia_reference"
    assert find_recipe(tmp_path, "rosalia", "rosalia_reference") == path


def test_create_recipe_keeps_an_existing_file(tmp_path: Path) -> None:
    path = create_recipe(tmp_path, "rosalia", "ref")
    path.write_text("edited\n")
    with pytest.raises(FileExistsError):
        create_recipe(tmp_path, "rosalia", "ref")
    assert path.read_text() == "edited\n"
    create_recipe(tmp_path, "rosalia", "ref", overwrite=True)
    assert path.read_text() != "edited\n"


def test_template_becomes_a_valid_recipe_once_filled_in() -> None:
    data = yaml.safe_load(TEMPLATE_PATH.read_text())
    data.update(
        name="ref",
        site="ROS",
        agency="TUW",
        fields=[
            {"skip": 4},
            {"doy": 3},
            {"hour_letter": 1},
            {"minute": 2},
            {"skip": 1},
            {"yy": 2},
            {"skip": 1},
        ],
    )
    recipe = NamingRecipe.model_validate(data)
    assert recipe.to_virtual_file(Path("rref001a15.25o")).canonical_str == (
        "ROSR01TUW_R_20250010015_15M_05S_AA.rnx"
    )
