import os
import re


def read_env():
    """
    Read environment variables from a .env file.
    
    Taken from https://gist.github.com/bennylope/2999704.
    """
    try:
        env_file = os.path.join(os.path.dirname(__file__), '../../.env')
        with open(env_file) as f:
            content = f.read()
    except IOError:
        return

    for line in content.splitlines():
        m1 = re.match(r'\A([A-Za-z_0-9]+)=(.*)\Z', line)
        if m1:
            key, val = m1.group(1), m1.group(2)
            m2 = re.match(r"\A'(.*)'\Z", val)
            if m2:
                val = m2.group(1)
            m3 = re.match(r'\A"(.*)"\Z', val)
            if m3:
                val = re.sub(r'\\(.)', r'\1', m3.group(1))
            os.environ[key] = val
