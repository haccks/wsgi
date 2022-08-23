from urllib.parse import parse_qsl


def view(request):
    """A simple view method
    
    View to handle GET and POST requests. It can handle:
    1. GET with or without query parameters
    2. GET requesting html file
    3. GET requesting with an image file
    4. GET requesting a form
    5. POST submitting a form
    6. 404

    :param request: http request
    :return: A tuple of response, HTTP status code as byte string
    """

    if request['method'] == 'GET':
        if request['path'] == '/':              # Transfer simple byte string
            return response_encode(f"Hello from {request['path']}. Methods is {request['method']}", '200 OK')
        if request['path'] == '/index':

            if request['query_param']:          # get query parameters and send it back
                return response_encode(f"{request['query_param']}", '200 OK')
            else:                               # Transfer a html file
                return read_file(f"{request['path'][1:]}.html", 'r')
        if request['path'].endswith(('.png', '.jpeg')):    # Transfer an image
            return read_file(request['path'][1:], 'rb')
        if request['path'] == '/form':
            return read_file(f"{request['path'][1:]}.html", 'r')

    if request['method'] == 'POST':             # Handle a post request
        # When the request method is POST the query string will be sent in the
        # HTTP request body in instead of in the URL. The request body is in
        # the WSGI server supplied wsgi.input file like environment variable.

        try:
            request_body_size = int(request['content_length'], 0)
        except ValueError:  # if CONTENT_LENGTH missing
            request_body_size = 0

        request_body = request['body'].read(request_body_size)
        params = get_post_params(request_body)
        res_body = f"User <b>{params['user_name']}</b> left a message <i>{params['user_message']}</i>"
        return response_encode(res_body, '200 OK')

    return response_encode('<b>404 Not Found :(</b>', '404 Not Found')


# Helper functions
# ---------------------------
def read_file(file_path, mode):
    """Read file

    :param file_path: file path
    :param mode: file mode
    :return: List of byte string of file data
    """

    with open(file_path, mode) as f:
        fdata = f.read()
    return response_encode(fdata, '200 OK')


def response_encode(body, status):
    """Encode response

    Convert the body and status code of response to byte string.
    :param body: response body
    :param status: Standard HTTP status code
    :return: List of byte strings
    """

    return [
        body if isinstance(body, bytes) else (body+'\r\n').encode('utf-8'),
        status.encode('utf-8')
    ]


def get_post_params(request_body):
    """Populate a dictionary with the payload of POST request

    Parse payload data of POST request and populate a dictionary
    with the passed parameters.
    :param request_body: payload
    :return: Dictionary of POST method parameters
    """

    if request_body:
        params = dict(parse_qsl(request_body))
        return params

