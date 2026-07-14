# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/nfb2021/canvodpy-extensions/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                 |    Stmts |     Miss |   Cover |   Missing |
|--------------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| packages/canvod-adapters/src/canvod/adapters/\_\_init\_\_.py         |        2 |        0 |    100% |           |
| packages/canvod-adapters/src/canvod/adapters/gnssvod/\_\_init\_\_.py |        4 |        0 |    100% |           |
| packages/canvod-adapters/src/canvod/adapters/gnssvod/convert.py      |      187 |       99 |     47% |66-109, 145-161, 177-197, 255-286, 326-355, 465, 551 |
| packages/canvod-adapters/src/canvod/adapters/gnssvod/io.py           |       30 |       21 |     30% |25-37, 69-77, 123-128 |
| packages/canvod-adapters/src/canvod/adapters/gnssvod/provenance.py   |       20 |        0 |    100% |           |
| packages/canvod-airflow/src/canvod/airflow/\_\_init\_\_.py           |        1 |        0 |    100% |           |
| packages/canvod-filemap/src/canvod/filemap/\_\_init\_\_.py           |        8 |        0 |    100% |           |
| packages/canvod-filemap/src/canvod/filemap/config\_models.py         |       23 |        0 |    100% |           |
| packages/canvod-filemap/src/canvod/filemap/convention.py             |       73 |        0 |    100% |           |
| packages/canvod-filemap/src/canvod/filemap/mapping.py                |      182 |       18 |     90% |83-86, 146-148, 180-182, 215-217, 229, 236, 244, 263, 372 |
| packages/canvod-filemap/src/canvod/filemap/patterns.py               |       45 |        0 |    100% |           |
| packages/canvod-filemap/src/canvod/filemap/recipe.py                 |      123 |        7 |     94% |230-234, 240-244, 265, 321-322 |
| packages/canvod-filemap/src/canvod/filemap/validator.py              |       61 |        6 |     90% |97, 109-110, 119, 146, 156 |
| **TOTAL**                                                            |  **759** |  **151** | **80%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/nfb2021/canvodpy-extensions/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/nfb2021/canvodpy-extensions/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/nfb2021/canvodpy-extensions/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/nfb2021/canvodpy-extensions/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fnfb2021%2Fcanvodpy-extensions%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/nfb2021/canvodpy-extensions/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.