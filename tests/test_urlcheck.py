import socket

import pytest

from gateway.urlcheck import UrlRejected, check_upstream_url


def resolver_for(*addresses):
    """A fake name lookup that answers with the given addresses."""

    def resolve(hostname, port):
        return [(2, 1, 6, "", (address, 0)) for address in addresses]

    return resolve


def never_called(hostname, port):
    raise AssertionError("the name should not have been looked up")


def test_a_public_address_is_accepted():
    check_upstream_url("https://tools.example.com/mcp", set(), resolver_for("93.184.216.34"))


def test_a_private_address_is_refused():
    with pytest.raises(UrlRejected):
        check_upstream_url("http://internal.example.com/mcp", set(), resolver_for("10.0.0.5"))


def test_loopback_is_refused_unless_the_operator_allows_it():
    with pytest.raises(UrlRejected):
        check_upstream_url("http://127.0.0.1:8101/mcp", set(), resolver_for("127.0.0.1"))
    check_upstream_url("http://127.0.0.1:8101/mcp", {"127.0.0.1"}, never_called)


def test_the_cloud_secret_data_address_is_refused():
    with pytest.raises(UrlRejected):
        check_upstream_url("http://169.254.169.254/", set(), resolver_for("169.254.169.254"))


@pytest.mark.parametrize("url", ["ftp://example.com/x", "file:///etc/passwd"])
def test_only_http_and_https_are_allowed(url):
    with pytest.raises(UrlRejected):
        check_upstream_url(url, set(), never_called)


def test_a_user_name_or_password_in_the_address_is_refused():
    with pytest.raises(UrlRejected):
        check_upstream_url("http://admin:secret@example.com/mcp", set(), never_called)


def test_a_name_that_does_not_exist_is_refused():
    def cannot_find(hostname, port):
        raise socket.gaierror("no such name")

    with pytest.raises(UrlRejected):
        check_upstream_url("http://nowhere.invalid/mcp", set(), cannot_find)


def test_one_private_answer_among_public_ones_is_enough_to_refuse():
    with pytest.raises(UrlRejected):
        check_upstream_url("http://tricky.example.com/mcp", set(), resolver_for("93.184.216.34", "10.0.0.5"))


def test_a_loopback_address_hidden_inside_an_ipv6_address_is_refused():
    with pytest.raises(UrlRejected):
        check_upstream_url("http://sneaky.example.com/mcp", set(), resolver_for("::ffff:127.0.0.1"))