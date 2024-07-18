# windstorm
SysML 2.0 Analysis Toolset

[![PyPI version](https://badge.fury.io/py/sysml-windstorm.svg)](https://badge.fury.io/py/sysml-windstorm)[![PyPI status](https://img.shields.io/pypi/status/sysml-windstorm.svg)](https://pypi.python.org/pypi/sysml-windstorm/)[![Coverage Status](https://coveralls.io/repos/github/Westfall-io/windstorm/badge.svg)](https://coveralls.io/github/Westfall-io/windstorm)![Docstring Coverage](https://raw.githubusercontent.com/Westfall-io/windstorm/main/doc-cov.svg)[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

## Jinja Usage
Any text based file (.json, .py, .txt, .m) can be templated with [Jinja](https://jinja.palletsprojects.com).

```
{{ windstorm('myVar') }}
```

Versions after 0.4.0 support Excel files, even though they are not pure text.

## SysMLv2 API
When pointed at an appropriate SysMLv2 API, windstorm will pull all of the
parameters for use in the jinja templates.

```
windstorm -a http://your_api_address:9000 -p project_uuid element_name
```
