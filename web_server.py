"""WSGI server side

WSGI complaint web server which takes http request
from client (user agent) and responsible for returning corresponding http response.
It is a small http web server (or application server) just like gunicorn or uWSGI,
but very minimal :).
"""


import socket
import io
import sys
from datetime import datetime

import wsgi

HOST = 'localhost'
PORT = 8080


def handle_request():
    """Entry point of the server (WSGI complaint).

    This basically does the following:
    1. Listen and accept requests using Unix sockets
    2. Parse received http requests
    3. Create a dictionary containing CGI like variables
    4. Invoke the application object provided by applications side of WSGI interface
    5. Finally, send back the http response to the client
    6. It also provides a closure like callback method that takes sttp status
        and http response header as an argument
    """

    with socket.socket() as soc:
        soc.bind((HOST, PORT))

        def start_response(status, headers):
            """Callback method

            Send back the HTTP status code and response header as byte string over
            the socket to the client. It uses the same connection object as the
            enclosing function.
            :param status: Standard HTTP status code
            :param headers: Standard HTTP response header
            """

            conn.sendall(f'HTTP/1.1 {status}\r\n'.encode('utf-8'))
            for (key, value) in headers:
                conn.sendall(f'{key}: {value}\r\n'.encode('utf-8'))
            conn.sendall('\r\n'.encode('utf-8'))

        try:
            while True:
                soc.listen(1)
                conn, addr = soc.accept()
                with conn:
                    # Get raw http request from client
                    http_request = conn.recv(102400).decode('utf-8')
                    # Parse the request
                    request = parse_http_request(http_request)
                    # Create environ dictionary using the parsed request
                    environ = to_environ(*request)
                    # call the application callable of the app
                    response = wsgi.application(environ, start_response)
                    # http_response = process_response(response)
                    # Return response to the client
                    for data in response:
                        conn.sendall(data)
                    # conn.sendall('\r\n'.encode('utf-8'))

        # Exit gracefully without traceback.
        except KeyboardInterrupt:
            print('Server stopped.')
            sys.exit(1)


# Helper functions
# ---------------------------
def parse_http_request(http_request):
    """A simple HTTP request parser

    Break down the raw HTTP request into pieces.
    HTTP request format:
    GET / HTTP/1.1
    host: localhost:8080
    User-Agent: curl/7.54.0
    Content-Length: 30
    ...

    body

    :param http_request: Standard HTTP request
    :return: Return a tuple of 5 objects containing parts of HTTP request
    """

    request_line, *headers, _, body = http_request.splitlines()
    method, path, protocol = request_line.split(' ')
    headers = dict(
        line.split(':', maxsplit=1) for line in headers
    )

    return method, path, protocol, headers, body


def to_environ(method, path, protocol, headers, body):
    """Populate and return a dictionary

    Populate and return a dictionary with CGI like variables for each
    received request from the client. In simple word:
    it de-assemble the raw HTTP request into a dictionary.
    :param method: HTTP method
    :param path: URI
    :param protocol: HTTP protocol
    :param headers: standard HTTP request headers
    :param body: payload
    :return: A Dictionary containing CGI like variables
    """

    return {
        'REQUEST_METHOD': method,
        'PATH_INFO': path.split('?')[0] if '?' in path else path,
        'SERVER_PROTOCOL': protocol,
        'QUERY_STRING': get_query_string(path),
        'wsgi.input': io.StringIO(body),  # Must be a file-like object and io.StringIO returns-file like object
        'CONTENT_LENGTH': headers['Content-Length'] if 'Content-Length' in headers else None
        # format_headers(headers)
    }


def get_query_string(path):
    """
    Extract the query string passed in the GET request from the URI.
    :param path: URI
    :return: Query string (ex: 'name=Dan%20Khan&country=IN')
    """

    if '?' in path:
        _, query_string = path.split('?')
        return query_string
    return None


if __name__ == '__main__':
    now = datetime.now().strftime('%B %d, %Y %H:%M:%S')
    print(
        f"{now}"
        f"\nStarting development server at http://{HOST}:{PORT}/" 
        "\nQuit the server with CONTROL-C."
    )
    handle_request()
