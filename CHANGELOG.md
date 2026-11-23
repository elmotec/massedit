## v0.72.0 (2026-10-27)


- target Python 3.15 and drop Python 3.10 support (#34)

## v0.71.0 (2025-09-21)

### BREAKING CHANGES

- **drop Python support below 3.10**: Minimum Python version is now 3.10
- **remove Python 2/3 compatibility code**: Removed unicode compatibility layer

## v0.70.0 (2023-08-31)

### Fix

- fix commitizen configuration
- fix .github/workflows/python-app.yml (#18)

## v0.69.1 (2020-12-22)

- Updated infrastructure files to setup.cfg/pyproject.toml instead of setup.py. Thanks @isidroas.

## v0.69.0 (2020-12-22)

- Moved CI from Travis to GitHub workflows and added regression tests for Python 2.7.

## v0.68.6 (2019-12-02)

- Added support for Python 3.8 and stdin input via the `-` argument.
- Documented a regex to turn base classes into Google Mock `MOCK_METHOD`.

## v0.68.5 (2019-04-13)

- Added the `--newline` option to force newline output. Thanks @ALFNeT!

## v0.68.4 (2017-10-24)

- Fixed a bug that could cause changes to be missed when `-w` was omitted. Thanks @tgoodlet!

## v0.68.3 (2017-09-20)

- Added `--generate` to create a `fixer.py` template for use with `-f fixer.fixit`.
- Added official support for Python 3.6.

## v0.68.1 (2016-06-04)

- Fixed encoding issues when processing non-ASCII files.
- Added `--encoding` to force the encoding value.
- Listed support for Python 3.5.

## v0.67.1 (2015-06-28)

- Documentation fixes.

## v0.67 (2015-06-23)

- Added the `file_name` argument to processing functions.
- Fixed incorrect closing of `sys.stdout` and `sys.stderr`.
- Improved diagnostics when the processing function does not take two arguments.
- Swapped `-v` and `-V` to be consistent with Python.
- Pylint fixes.
- Added support for Python 3.4 and dropped support for Python 3.2.

## v0.66 (2013-07-14)

- Fixed a lost executable bit with the `-f` option. Thanks @myint!

## v0.65 (2013-07-12)

- Added `-f` to execute code in a separate file or module.
- Added Travis CI and fixed Python 2.7 support. Thanks @myint!

## v0.64 (2013-06-01)

- Fixed `setup.py` so massedit installs as a script and fixed end-of-line issues. Thanks @myint!

## v0.63 (2013-05-27)

- Renamed the project to massedit. Previous versions were known as Python-Mass-Editor.

## v0.62 (2013-04-11)

- Fixed an `EditorError` raised when an expression returned an empty string.

## v0.61 (2012-07-06)

- Added `massedit.edit_files` for library use instead of command-line use. Suggested by Maxim Veksler.

## v0.60 (2012-07-04)

- Treated arguments as patterns rather than files to ease processing multiple files in subdirectories.
- Added `-s` for the start directory and `-m` for the maximum depth.

## v0.52 (2012-06-05)

- Upgraded for Python 3 while retaining Python 2.7 compatibility.

## v0.51 (2012-05)

- Initial beta release.
