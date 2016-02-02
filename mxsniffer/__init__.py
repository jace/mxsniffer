# -*- coding: utf-8 -*-

"""
MX Sniffer identifies common email service providers given an email address or a domain name.
"""

from __future__ import absolute_import
from urlparse import urlparse
from email.utils import parseaddr
import dns.resolver

from ._version import __version__, __version_info__  # NOQA
from .providers import providers

__all__ = ['MXLookupException', 'get_domain', 'mxsniff']


provider_domains = {}

for name, domains in providers.items():
    for domain in domains:
        provider_domains[domain.lower()] = name


class MXLookupException(Exception):
    pass


def get_domain(email_or_domain):
    """
    Extract domain name from an email address, URL or (raw) domain name.

    >>> get_domain('example@example.com')
    'example.com'
    >>> get_domain('http://www.example.com')
    'www.example.com'
    >>> get_domain('example.com')
    'example.com'
    """
    if '@' in email_or_domain:
        # Appears to be an email address.
        name, addr = parseaddr(email_or_domain)
        domain = addr.split('@', 1)[-1]
    elif '//' in email_or_domain:
        domain = urlparse(email_or_domain).netloc.split(':')[0]
    else:
        domain = email_or_domain
    return domain


def mxsniff(email_or_domain):
    """
    Lookup MX records for a given email address, URL or domain name and identify the email service provider(s)
    from an internal list of known service providers.

    :param str email_or_domain: Email, domain or URL to lookup
    :return: List of identified service providers, typically zero or one, but possibly more in unusual circumstances

    >>> mxsniff('example.com')
    []
    >>> mxsniff('example@gmail.com')
    ['google-gmail']
    >>> mxsniff('https://google.com/')
    ['google-apps']
    >>> mxsniff('__invalid_domain_name__.com')
    []
    """
    domain = get_domain(email_or_domain)

    result = []

    try:
        answers = sorted([(rdata.preference, rdata.exchange.to_text(omit_final_dot=True).lower())
            for rdata in dns.resolver.query(domain, 'MX')])
        for preference, exchange in answers:
            if exchange in provider_domains:
                provider = provider_domains[exchange]
                if provider not in result:
                    result.append(provider)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        pass
    except dns.exception.DNSException as e:
        raise MXLookupException('{exc} {error}'.format(exc=e.__class__.__name__, error=unicode(e)))

    return result
