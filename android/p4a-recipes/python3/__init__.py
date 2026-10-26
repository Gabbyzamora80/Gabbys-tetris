from pathlib import Path

from pythonforandroid import recipe as recipe_module
from pythonforandroid.util import load_source

p4a_root = Path(recipe_module.__file__).resolve().parent.parent
upstream_recipe = p4a_root / "recipes" / "python3" / "__init__.py"
upstream = load_source(
    "pythonforandroid.recipes.python3_upstream",
    str(upstream_recipe),
)


class Python3Recipe(upstream.Python3Recipe):
    # CPython 3.12 enables grp when it sees getgrgid, but Android's NDK lacks
    # getgrent. This app does not use grp, so mark the extension unavailable.
    configure_args = upstream.Python3Recipe.configure_args + [
        "py_cv_module_grp=n/a",
    ]


recipe = Python3Recipe()
