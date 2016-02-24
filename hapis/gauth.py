#---------------------------------------------------------------------------
# One time password algorithms
#---------------------------------------------------------------------------
"""
This is a wrapper for TOTP (Time-based One Time Passwords) RFC6238 cf
HOTP (HMAC (Hashed Message Authentication Code) One Time Passwords) RFC4226.
Uses onetimepass.  See also passlib.totp and otpauth.
"""

from base64 import b32encode
from hashlib import sha1
from io import BytesIO
from passlib.utils import rng, getrandbytes
import qrcode
from .onetimepass import valid_totp

try:
    from .secret import _grassmere
except ImportError:
    _grassmere = "23456789abcdef543210"

def genKey():
    rawKey = getrandbytes(rng, 10)
    hexKey = "".join("{:02x}".format(byte) for byte in rawKey)
    return hexKey

def getSecret(gauthKey, userId):
    #TODO use to_bytes?
    data = BytesIO()
    for i in range(0, 20, 2):
        data.write(bytes([int(gauthKey[i:i+2], 16)]))
    idx = (userId * 20) % len(_grassmere)
    for i in range(idx, idx+20, 2):
        data.write(bytes([int(_grassmere[i:i+2], 16)]))
    hashed = sha1(data.getvalue()).digest()
    return b32encode(hashed).decode()

def getUri(secret, loginname):
     issuer = "Cream"
     # see http://code.google.com/p/google-authenticator/wiki/KeyUriFormat
     uri = "otpauth://totp/{issuer}:{loginname}?"\
           "secret={secret}&issuer={issuer}".format(**locals())
     return uri

def getQRCode(gauthKey, user):
    secret = getSecret(gauthKey, user.id)
    data = BytesIO()
    qrcode.make(getUri(secret, user.loginname), box_size=6).save(data)
    return data.getvalue()

def verifyOneTimePassword(givenOtp, secret):
    """just a wrapper around valid_totp"""
    return valid_totp(givenOtp, secret)

