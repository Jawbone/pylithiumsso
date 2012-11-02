Requires pycrypto.

Initialize the client with client information:

```
    from pylithiumsso.client import LithiumClient

    client_id = "some_id"
    client_domain = ".example.com"
    secret_key = "super_secret"
    settings = {
        "foo": "bar",
        "bar": "baz"
    }

    client = LithiumClient(client_id, client_domain, secret_key, settings)

    user_id = "some_unique_id"
    username = "some_username"
    email = "foo@bar.com"

    # Typically, you would acquire these things from your app server's request
    # object

    user_agent = "Mozilla/5.0"
    http_referer = "localhost"
    remote_address = "127.0.0.1"
    cookie_name, cookie_value = client.get_sso_cookie(user_id, username, email,
                                                    user_agent, http_referer,
                                                    remote_address)

```

To decode a provided cookie value:

```

    from pylithiumsso.client import LithiumClient

    client_id = "some_id"
    client_domain = ".example.com"
    secret_key = "super_secret"
    settings = {
        "foo": "bar",
        "bar": "baz"
    }

    client = LithiumClient(client_id, client_domain, secret_key, settings)

    cookie_dict = client.decode(client.secret_key, "lithium_encoded_cookie")

```
