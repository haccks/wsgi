"""WSGI compliant application side.

Basically frameworks (like django/flask) implement it. As per WSGI
specifications it must define a callable object with signature:
"app(environ, start_response)"
and this method suppose to call the
start_response callback. Check PEP3333 for more info:
https://peps.python.org/pep-3333/
"""

import importlib
from urllib.parse import parse_qsl
from datetime import datetime

import views

HOT_RELOAD = True


def application(environ, start_response):
    """Entry point of the application side

    Required application object (callable) as per WSGI specifications.
    It must call the callback method passed as argument by the server
    side before returning the response.
    :param environ: A Dictionary containing CGI like variables
    :param start_response: Callback method passed from server side
    :return: The response body as "byte strings wrapped in an iterable"
    """

    request = prepare_request(environ)
    mod = importlib.reload(views) if HOT_RELOAD else views
    response, status = mod.view(request)
    console_log(request, status)
    response_headers = get_headers(environ, response)
    start_response(status, response_headers)
    return [response]


# Helper functions
# ---------------------------
def prepare_request(environ):
    """Populate a dictionary with the value of the dictionary passed.

    :param environ: A Dictionary containing CGI like variables
    :return: A dictionary containing de-assembled HTTP request.
    """

    return {
        'method': environ['REQUEST_METHOD'],
        'path': environ['PATH_INFO'],
        'query_param': get_query_params(environ['QUERY_STRING']),
        'protocol': environ['SERVER_PROTOCOL'],
        'body': environ['wsgi.input'],
        'content_length': environ['CONTENT_LENGTH']
    }


def get_query_params(query_string):
    """
    Populate a dictionary by parsing the query string passed in a
    GET request.
    :param query_string: Query string passed in GET request
    :return: A dictionary of query parameters in query string
    """

    if query_string:
        # params = dict(param.split('=') for param in query_string.split('&'))
        # parse_qsl will use either unquote or unquote_plus for + and %20 in query param
        params = dict(parse_qsl(query_string))
        return params
    return None


def get_headers(environ, response):
    """Prepare and return standard HTTP headers.

    :param environ: A Dictionary containing CGI like variables
    :param response: Response returned by the view
    :return: List od standard HTTP headers
    """

    fext = None
    if environ['PATH_INFO'].endswith(('.png', '.jpeg')):
        fext = environ['PATH_INFO'].split('.')[-1]
    content_type = ('Content-Type', f'image/{fext}') if fext else ('Content-Type', 'text/html')
    return [
        content_type,
        ('Content-Length', str(len(response)))
        # list goes on ....
    ]


def console_log(request, status):
    """Print log on stdin

    Logs the date time and request line for each incoming request on
    the stdout along with response status code.
    :param request: HTTP request
    :param status: Standard HTTP status code
    """

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] \"{request['method']} {request['path']} {request['protocol']}\" {status.decode()}")
