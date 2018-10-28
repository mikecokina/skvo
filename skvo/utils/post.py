def get_post_data(request):
    """
    get incoming post data from django rest request

    :param request: rest_framework.request.Request
    :return: dict
    """
    try:
        data = request.data
    except:
        raise ValueError('Error in try to parse post json data')
    if data is None:
        raise LookupError('Post data are missing')
    return data
