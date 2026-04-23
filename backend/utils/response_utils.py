from flask import jsonify


def success_response(data=None, message='', status_code=200):
    """Return a standardised success JSON envelope."""
    body = {
        'success': True,
        'data': data,
        'message': message,
    }
    return jsonify(body), status_code


def error_response(message='An error occurred', status_code=400):
    """Return a standardised error JSON envelope."""
    body = {
        'success': False,
        'data': None,
        'message': message,
    }
    return jsonify(body), status_code


def paginated_response(items, total, limit, offset):
    """Return a paginated list response."""
    body = {
        'success': True,
        'data': {
            'items': items,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total,
        },
        'message': '',
    }
    return jsonify(body), 200
