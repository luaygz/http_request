from requests.structures import CaseInsensitiveDict
from urllib.parse import urlparse, parse_qs
import requests_raw
import json

class HTTPRequest:
	"""
	Represents an HTTP request.
	"""
	
	default_schemes_to_ports = {
		"http": 80,
		"https": 443
	}

	def __init__(self, _scheme: str = "https", url: str = None, raw: str = None, file: str = None):
		"""
		Args:
			scheme (str, optional): The scheme of the request (e.g. "http", "https")
			url (str, optional): The URL of the request (e.g. "https://example.com/path?query#fragment")
			raw (str, optional): The raw HTTP request
			file (str, optional): The path to a file containing the raw HTTP request

		Note:
			Can provide one of `url`, `raw`, or `file`. The other arguments will be ignored.
			If `raw` or `file` is provided, it must follow the HTTP request spec and contain a Host header.
		"""
		self.method: str = "GET"
		self.path: str = "/"
		self.query: dict = {}
		self.fragment: str = ""
		self.version: str = "HTTP/1.1"
		self.scheme: str = _scheme
		self.headers: CaseInsensitiveDict = CaseInsensitiveDict()
		self.body: str = ""

		if url:
			self.url = url
		elif raw:
			self.parse(raw)
		elif file:
			with open(file, "r") as f:
				self.parse(f.read())

	@property
	def port(self) -> int:
		"""
		Constructed from the Host header, or the default port for the scheme if the Host header does not contain a port.
		"""
		if not "Host" in self.headers:
			raise ValueError("Host header is missing")
		if ":" in self.headers["Host"]:
			return int(self.headers["Host"].split(":")[1])
		else:
			return self.default_schemes_to_ports[self.scheme]
	
	@port.setter
	def port(self, _port: str | int) -> None:
		"""
		Args:
			_port (str | int): The port to set the request to
		
		Sets:
			The port of the request and the Host header

		Note:
			If `_port` is a default port for the scheme (e.g. 80 for http, 443 for https), the port will not be included in the Host header.
		"""
		if not "Host" in self.headers:
			raise ValueError("Host header is missing")
		# only add port if it's not the default port for the scheme (e.g. 80 for http, 443 for https)
		if int(_port) != self.default_schemes_to_ports.get(self.scheme, None):
			self.headers["Host"] = f"{self.host}:{str(_port)}"
		else:
			self.headers["Host"] = f"{self.host}" # port is default, so don't include it

	@property
	def host(self) -> str:
		"""
		Constructed from the Host header
		"""
		if not "Host" in self.headers:
			raise ValueError("Host header is missing")
		return self.headers["Host"].split(":")[0]

	@host.setter
	def host(self, _host: str) -> None:
		"""
		Args:
			_host (str): The host to set the request to
		
		Note:
			If the port is a default port for the scheme (e.g. 80 for http, 443 for https), the port will not be included in the Host header.
		"""
		# only add port if it's not the default port for the scheme (e.g. 80 for http, 443 for https)
		if self.port != self.default_schemes_to_ports.get(self.scheme, None):
			self.headers["Host"] = f"{_host}:{str(self.port)}"
		else:
			self.headers["Host"] = _host
	
	@property
	def url(self) -> str:
		"""
		Constructed from the scheme, host, port, path, query, and fragment

		Note:
			If the port is a default port for the scheme (e.g. 80 for http, 443 for https), the port will not be included in the URL.
		"""
		_url = f"{self.scheme}://{self.host}"
		# only add port if it's not the default port for the scheme (e.g. 80 for http, 443 for https)
		if self.port != self.default_schemes_to_ports.get(self.scheme, None):
			_url += f":{str(self.port)}"
		_url += self.path
		if self.query:
			_query = "&".join([f"{key}={value}" for key, value in self.query.items()])
			_url += f"?{_query}"
		if self.fragment:
			_url += f"#{self.fragment}"
		return _url
	
	@url.setter
	def url(self, _url: str) -> None:
		"""
		Args:
			_url (str): The URL to set the request to

		Note:
			The URL must have a scheme.
		"""
		url_parsed = urlparse(_url)
		if not url_parsed.scheme:
			raise ValueError("URL must have a scheme")
		self.scheme, self.headers["Host"], self.path, _, self.query, self.fragment = url_parsed
	
	def __getitem__(self, key: str) -> str:
		"""
		Args:
			key (str): The body's json or form key to get the value of

		Returns:
			The value of the body's json or form key
		
		Note:
			If the body is not json or form, a ValueError will be raised.

		"""
		if self.headers.get("Content-Type", None) == "application/json":
			return json.loads(self.body).get(key, None)
		elif self.headers.get("Content-Type", None) == "application/x-www-form-urlencoded":
			value = parse_qs(self.body).get(key, None)
			return value[0] if value else None
		else:
			raise ValueError("Body is not json or form")
	
	def __setitem__(self, key: str, value: str) -> None:
		"""
		Args:
			key (str): The body's json or form key to set the value of
			value (str): The value to set the body's json or form key to

		Note:
			If the body is not json or form, a ValueError will be raised.
		"""
		if self.headers.get("Content-Type", None) == "application/json":
			body = json.loads(self.body)
			body[key] = value
			self.body = json.dumps(body)
		elif self.headers.get("Content-Type", None) == "application/x-www-form-urlencoded":
			# parse_qs returns a list of values, so we'll just take the first one
			body = {key: value[0] for key, value in parse_qs(self.body).items()}
			body[key] = value
			self.body = "&".join([f"{key}={value}" for key, value in body.items()])
		else:
			raise ValueError("Body is not json or form")
	
	def __delitem__(self, key: str) -> None:
		"""
		Args:
			key (str): The body's json or form key to delete

		Note:
			If the body is not json or form, a ValueError will be raised.
		"""
		if self.headers.get("Content-Type", None) == "application/json":
			body = json.loads(self.body)
			del body[key]
			self.body = json.dumps(body)
		elif self.headers.get("Content-Type", None) == "application/x-www-form-urlencoded":
			body = {key: value[0] for key, value in parse_qs(self.body).items()}
			del body[key]
			self.body = "&".join([f"{key}={value}" for key, value in body.items()])
		else:
			raise ValueError("Body is not json or form")

	def __str__(self) -> str:
		"""
		Returns:
			The raw HTTP request

		Note:
			The HTTP request spec specifies line breaks should be CRLF, so they will be converted to CRLF.
		"""
		_path = self.path
		if self.query:
			_query = "&".join([f"{key}={value}" for key, value in self.query.items()])
			_path += f"?{_query}"
		if self.fragment:
			_path += f"#{self.fragment}"

		raw = f"{self.method} {_path} {self.version}\n"
		for header in self.headers:
			raw += f"{header}: {self.headers[header]}\n"
		raw += "\n"
		raw += self.body
		raw = raw.replace("\n", "\r\n") # HTTP request spec requires CRLF
		return raw

	def __repr__(self) -> str:
		return self.__str__()

	def parse(self, raw: str) -> None:
		"""
		Args:
			raw (str): The raw HTTP request
		"""
		# normalize request
		if "\r" in raw:
			raw = raw.replace("\r", "") # HTTP request spec requires CRLF, but we'll be lenient
		raw = raw.strip()
		
		# parse request line
		request_line, headers_and_body = raw.split("\n", 1)
		self.method, self.path, self.version = request_line.split(" ")
		if "?" in self.path:
			self.path, self.query = self.path.split("?", 1)

		# parse headers
		if "\n\n" in headers_and_body:
			headers_raw, self.body = headers_and_body.split("\n\n", 1)
		else:
			headers_raw = headers_and_body

		for header in headers_raw.split("\n"):
			key, value = header.split(":", 1)
			self.headers[key.strip()] = value.strip()
		
		if "Host" not in self.headers:
			raise ValueError("Host header is missing")
	
	def send(self, **kwargs):
		"""
		Args:
			kwargs: Keyword arguments to pass to `requests_raw.raw`

		Returns:
			The response from `requests_raw.raw`

		Note:
			The HTTP spec requires a Host header, so a ValueError will be raised if the Host header is missing.
			The Content-Length header will be set to the length of the body.
		"""
		if "Host" not in self.headers:
			raise ValueError("Host header is missing")
		
		self.headers["Content-Length"] = len(self.body)
		return requests_raw.raw(url=self.url, data=self.__str__().encode("utf-8"), **kwargs)