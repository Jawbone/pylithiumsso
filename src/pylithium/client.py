import base64
import binascii
import random
import string
import time
import zlib

from Crypto.Cipher import AES

_CRYPTO_BAD_CHARS = "+/="
_CRYPTO_GOOD_CHARS = "-_."
ENCRYPT_REPLACE = string.maketrans(_CRYPTO_BAD_CHARS, _CRYPTO_GOOD_CHARS)
DECRYPT_REPLACE = string.maketrans(_CRYPTO_GOOD_CHARS, _CRYPTO_BAD_CHARS)
CRYPTO_BLOCK_SIZE = 16
CRYPTO_PADDING = '\0'
VECTOR_SPACE = string.digits + string.letters
COOKIE_NAME = "lithiumSSO:"
COOKIE_VERSION = "LiSSOv1.5"
COOKIE_FIELD_SEPARATOR = "|"
COOKIE_FIELD_ORDER = [
    "version",              # lithium version
    "server_id",            # server id (for "increasing randomness")
    "tsid",                 # random timestamp + 1
    "timestamp",            # timestamp of cookie creation
    "http_user_agent",      # user agent from request
    "http_referer",         # referer from request
    "http_remote_address",  # remote address from request
    "client_domain",        # requesting site's domain.
    "client_id",            # provided client id
    "unique_id",            # user's unique identifier
    "username",             # user's username
    "email_address",        # user's email address
    "settings"              # key=val settings string
]


class LithiumClient(object):

    def __init__(self, client_id, client_domain, secret_key, settings=None):
        self.client_id = client_id
        self.client_domain = client_domain
        self.secret_key = self._hexpack(secret_key)
        self.tsid = int(time.time()) * 1000
        self.settings = {} if settings is None else settings

    def get_sso_cookie(self, uid, username, email, user_agent, referer,
                       remote_addr, server_id=""):
        """ Formats and returns the cookie name and encrypted cookie. """
        server_id = self._parse_server_id(server_id, remote_addr)
        timestamp = "%s000" % int(time.time())
        cookie_values = {
            "version":              COOKIE_VERSION,
            "server_id":            server_id,
            "tsid":                 str(self.tsid + 1),
            "timestamp":            timestamp,
            "http_referer":         self._token_safe_string(referer),
            "http_user_agent":      self._token_safe_string(user_agent),
            "http_remote_address":  self._token_safe_string(remote_addr),
            "client_domain":        self.client_domain,
            "client_id":            self.client_id,
            "unique_id":            self._token_safe_string(uid),
            "username":             self._token_safe_string(username),
            "email_address":        self._token_safe_string(email),
            "settings":             self._parse_settings(self.settings)
        }

        # Generate it
        cookie_string = self._format_cookie(cookie_values)

        # Encrypt it
        encrypted_cookie = self.encode(self.secret_key, cookie_string)

        return self._cookie_name(self.client_id), encrypted_cookie

    @classmethod
    def _cookie_name(cls, client_id):
        """ Cookie name, in case the changes at some point. """
        return "%s%s" % (COOKIE_NAME, client_id)

    @classmethod
    def encode(cls, secret_key, unencoded):
        """ Uses CBC mode with an AES encryption encrypt a string. """
        iv = cls._get_random_initialization_vector()
        cipher = AES.new(secret_key, mode=AES.MODE_CBC, IV=iv)
        compressed = zlib.compress(unencoded)
        encrypted = base64.b64encode(cipher.encrypt(cls._pad(compressed)))
        encrypted = encrypted.translate(ENCRYPT_REPLACE)
        return "~2%s~%s" % (iv, encrypted)

    @classmethod
    def decode(cls, secret_key, encoded):
        """
        Uses CBC mode on AES encryption to decrypt a string with the key
        and initialization vector.
        """
        encoded_pieces = encoded.split("~")
        iv = encoded_pieces[1][1:]
        cipher = AES.new(secret_key, mode=AES.MODE_CBC, IV=iv)
        encoded_data = encoded_pieces[2]
        encoded_data = encoded_data.translate(DECRYPT_REPLACE)
        decrypted = cls._unpad(cipher.decrypt(base64.b64decode(encoded_data)))
        decrypted = zlib.decompress(decrypted)
        data_split = decrypted.split("|")
        settings_array = data_split[len(COOKIE_FIELD_ORDER):]
        index = len(settings_array) - 1
        settings_array[index] = settings_array[index].replace("iL", "")
        data_split = data_split[1:]

        decrypted_data = {}
        for i in range(len(COOKIE_FIELD_ORDER) - 1):  # Settings separately.
            datum = data_split[i]
            # If ID has a "-" in it from inception; don't need to replace here.
            if i != 1:
                datum = datum.replace("-", COOKIE_FIELD_SEPARATOR)
            decrypted_data[COOKIE_FIELD_ORDER[i]] = datum

        settings = {}
        for item in settings_array:
            _item = item.replace("-", COOKIE_FIELD_SEPARATOR)
            split_up = _item.split("=")
            if len(_item) and len(split_up) > 1:
                settings[split_up[0]] = split_up[1]
        decrypted_data["settings"] = settings
        return decrypted_data

    @classmethod
    def _unpad(cls, decrypted_string):
        """ Unpads string that was encrypted/padded with CRYPTO_PADDING. """
        return decrypted_string.rstrip(CRYPTO_PADDING)

    @classmethod
    def _pad(cls, encryption_string):
        """ Pads a string with CRYPTO_PADDING, using CRYPTO_BLOCK_SIZE. """
        string_length = len(encryption_string)
        padding = (CRYPTO_BLOCK_SIZE - string_length % CRYPTO_BLOCK_SIZE)
        padding *= CRYPTO_PADDING
        return encryption_string + padding

    @classmethod
    def _get_random_initialization_vector(cls, length=CRYPTO_BLOCK_SIZE):
        """
        Generates a random initialization vector for AES-CBC encryption
        using the provided length.
        """
        return ''.join(random.choice(VECTOR_SPACE) for i in xrange(length))

    @classmethod
    def _parse_server_id(cls, server_id, server_addr):
        """ Function to "increase randomness". """
        server_id = server_id.strip()

        if not server_id or not len(server_id):
            server_id = "34"  # Still not sure why this is a default.
        return '%s-%s' % (server_id, cls._gen_random_hex())

    @classmethod
    def _parse_settings(cls, settings_dict):
        """ Parses a settings array into a key=val string. """
        settings_data = ""
        for key, val in settings_dict.iteritems():
            if len(settings_data):
                settings_data += COOKIE_FIELD_SEPARATOR
            settings_data += "%s=%s" % (cls._token_safe_string(key),
                                        cls._token_safe_string(val))
        return settings_data

    @classmethod
    def _format_cookie(cls, cookie_data):
        """
        Uses COOKIE_FIELD_ORDER to format the cookie into a string of values
        separated by COOKIE_FIELD_SEPARATOR.

        This is as per the Lithium SSO documentation/spec for the data format.
        """
        cookie_string = "Li"
        for field in COOKIE_FIELD_ORDER:
            cookie_datum = cookie_data.get(field, "")
            cookie_string += "%s%s" % (COOKIE_FIELD_SEPARATOR, cookie_datum)

        cookie_string = "%siL" % cookie_string
        return cookie_string

    @classmethod
    def _hexpack(cls, hex_string):
        """
        Turns a plain-text hex string into a binary string.

        String must be hex chars only and an even length.
        """
        return binascii.unhexlify(hex_string)

    @classmethod
    def _gen_random_hex(cls, length=32):
        """ Generates a random hex string of given length. """
        # Why 32? I don't like magic numbers.
        random_vals = (
            random.choice(string.hexdigits).upper() for i in xrange(length))
        return "".join(random_vals)

    @classmethod
    def _token_safe_string(cls, token_string):
        """ Replaces any occurrences of COOKIE_FIELD_SEPARATOR. """
        safe_string = token_string.replace(COOKIE_FIELD_SEPARATOR, "-")
        return safe_string
