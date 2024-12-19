import os

EMAIL_ENABLED_IN_TEST_MODE = 'SERVICES_SENDMAIL_ENABLED_IN_TEST_MODE'

def enable_env_variable_in_test_mode(env_variable_name: str, func):
    """decorator function which will set an environment variable to enable calling SAP APIs in test mode
    and unset it after the test"""

    async def wrapper(*args, **kwargs):
        os.environ[env_variable_name] = 'true'
        await func(*args, **kwargs)
        os.environ.pop(env_variable_name)
    return wrapper


def enable_emailing_in_test_mode(func):
    """decorator function which will set an environment variable to enable emailing in test mode
    and unset it after the test"""

    env_variable_name = EMAIL_ENABLED_IN_TEST_MODE
    return enable_env_variable_in_test_mode(env_variable_name, func)
