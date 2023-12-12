HTTP_RESPONSE = {
    'SUCCESS_CODE': 200,
    'CREATED_CODE': 201,  # indicates that the request was successful and created a new page (url)
    'ACCEPTED_CODE': 202,  # indicates that the request is accepted but not completed
    'ERROR_FROM_USER_CODE': 400,
    'UNAUTHORIZED_CODE': 401,
    'ERROR_PAYMENT_CODE': 402,
    'FORBIDDEN_CODE': 403,
    'PAGE_NOT_FOUND_CODE': 404,
    'METHOD_NOT_ALLOWED_CODE': 405,  # (get, put, patch, post, delete...etc)
    'INTERNAL_ERROR_CODE': 500,
    'NOT_IMPLEMENTED_CODE': 501,  # useful when you want to tell the client that the function is not available yet
    'MESSAGE': {
        'SUCCESS_CODE': 'The request is done successfully!',
        'ERROR_FROM_USER_CODE': 'Error from user, please check your API parameters!',
        'ERROR_FROM_USER_CODE_1': 'We were not able to parse your path request,\n please check our API again to learn '
                                  'our pattern!',
        'UNAUTHORIZED_CODE': 'The user is not logged in, please login first!',
        'ERROR_PAYMENT_CODE': 'There is no Access-Key or Not Valid in Header!',
        'FORBIDDEN_CODE': 'The key already exists! You have to update, or delete the key then create again!',
        'PAGE_NOT_FOUND_CODE': 'The path does not exist!',
        'INTERNAL_ERROR_CODE': 'Sorry, there is an error from the database server due to your request, contact the '
                               'supplier!',
        'NOT_IMPLEMENTED_CODE': 'Sorry, the request with your parameters is not yet implemented, contact the supplier!',
    }
}
