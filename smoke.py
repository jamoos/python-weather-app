import requests
import pytest


def is_website_reachable(url):
    """Tests if the given website is reachable."""
    try:
        response = requests.get(url, timeout=50)  # Adjust timeout as needed
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


@pytest.mark.parametrize(
    "url, expected_result",
    [
        ("http://localhost:5000", True),
    ],
)
def test_website_reachability(url, expected_result):
    assert is_website_reachable(url) == expected_result


if __name__ == "__main__":
    pytest.main()

