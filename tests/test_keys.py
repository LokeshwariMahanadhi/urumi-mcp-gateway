from gateway.keys import hash_key, key_prefix, make_key


def test_keys_are_random_and_look_right():
    first, second = make_key(), make_key()
    assert first != second
    assert first.startswith("urumi_")
    assert len(first) == 49


def test_hash_is_stable_and_does_not_contain_the_key():
    key = make_key()
    assert hash_key(key) == hash_key(key)
    assert key not in hash_key(key)
    assert len(hash_key(key)) == 64


def test_prefix_is_the_start_of_the_key():
    key = make_key()
    assert key.startswith(key_prefix(key))
    assert len(key_prefix(key)) == 12