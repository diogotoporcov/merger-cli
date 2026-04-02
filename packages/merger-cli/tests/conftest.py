import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--merger-bin",
        action="store",
        default=None,
        help="Path to the merger binary to test"
    )

@pytest.fixture
def merger_bin(request):
    return request.config.getoption("--merger-bin")
