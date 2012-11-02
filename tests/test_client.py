from pylithium.client import LithiumClient
import random
import string


key_lengths = [32, 48, 64]
client_id = "example"
client_domain = ".example.com"
settings = {
    "foo": "baradsf",
    "bar": "baz"
}


def _gen_client(key_size):
    key_letters = [random.choice(string.hexdigits) for x in range(key_size)]
    client_key = "".join(key_letters)
    client = LithiumClient(client_id, client_domain, client_key, settings)
    return client


def test_encryption():

    for key_size in key_lengths:
        uid = "abcde|12345"
        email = "foo@bar.com"
        user_agent = "Mozilla"
        referer = "localhost"
        addr = "127.0.0.1"
        client = _gen_client(key_size)

        name, value = client.get_sso_cookie(uid, email, email, user_agent,
                                            referer, addr)

        #print "Encrypted Cookie: %s" % value

        decoded = client.decode(client.secret_key, value)
        assert decoded["client_id"] == client_id
        assert decoded["client_domain"] == client_domain
        assert decoded["unique_id"] == uid
        assert decoded["email_address"] == email
        assert decoded["username"] == email
        assert decoded["http_user_agent"] == user_agent
        assert decoded["http_referer"] == referer
        assert decoded["http_remote_address"] == addr

        decoded_settings = decoded["settings"]
        for key, val in decoded_settings.iteritems():
            assert key in settings
            assert decoded_settings[key] == settings[key]

        #print "Decrypted Cookie: %s" % decoded
        return True

