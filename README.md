# windstorm
SysML 2.0 Analysis Toolset

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
