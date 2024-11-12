import os


def get_conn_name():
    if os.environ.get('TEST_MODE', None) in ('true', 'True', 'TRUE', '1'):
        return 'conn_test'

    return 'conn_tenants'
