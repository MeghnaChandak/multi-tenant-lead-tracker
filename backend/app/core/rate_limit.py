from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by client IP. Good enough for a portfolio-scale deployment;
# a production system behind a proxy would key off X-Forwarded-For instead.
limiter = Limiter(key_func=get_remote_address)
