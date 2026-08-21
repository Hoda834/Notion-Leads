import requests
from urllib3.util.retry import Retry


def retrying_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=None,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session
