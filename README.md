# HTTPRequest
An HTTPRequest class and parser.



## Modifiable/default values

```
method: str = "GET"
path: str = "/"
query: dict = {}
fragment = ""
version: str = "HTTP/1.1"
scheme: str = scheme
headers: CaseInsensitiveDict = CaseInsensitiveDict()
body: str = "" # raw body text

"""
Can also treat the body as a dict if the Content-Type header specifies json or form data using square bracket notation ([]) on the HTTPRequest object directly
e.g. req["key1"] = "value1"
"""
```



## Usage

```python
from HTTPRequest import HTTPRequest
req = HTTPRequest(file="sample_requests/raw_http_request_POST.txt")
res = req.send()
print(res.text)

req.headers["header_key1"] = "header_value1" # modify or add header as dict
req.query["x"] = "y" # modify or add URL query value as dict
req["a"] = "b" # modify or add body value as dict (if json or form data, inferred from the Content-Type header)
res = req.send()
print(res.text)

req.body = "just some text" # can also directly set req.body to a raw value if Content-Type is not json or form data
```



## Content-Type Support

Right now, JSON, form data, and setting raw body data is supported. Things like multi-part form data are not currently supported and must be handled manually via setting the raw body text.

