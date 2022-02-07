import binascii
import os
import smtplib
from collections import namedtuple
from email.utils import parseaddr

import socks
from dns import resolver

from core.smtp import SocksSMTP as SMTP


class VerifyEmail:
    def __init__(self, email):
        self.email = email
        self.blocked_keywords = ["spamhaus",
                                 "proofpoint",
                                 "cloudmark",
                                 "banned",
                                 "blacklisted",
                                 "blocked",
                                 "block list",
                                 "denied"]

        self.proxy = {
            'socks4': socks.SOCKS4,
            'socks5': socks.SOCKS5,
            'http': socks.HTTP
        }

    def verify(self):
        class UnknownProxyError(Exception):
            def __init__(self, proxy_type):
                self.msg = f"The proxy type {proxy_type} is not known\n Try one of socks4, socks5 or http"

        class EmailFormatError(Exception):

            def __init__(self, msg):
                self.msg = msg

        class SMTPRecepientException(Exception):  # don't cover

            def __init__(self, code, response):
                self.code = code
                self.response = response

        def handle_550(response):
            if any([keyword.encode() in response for keyword in self.blocked_keywords]):
                return dict(message="Blocked by mail server- couldn't verify", deliverable=False, host_exists=True)
            else:
                return dict(deliverable=False, host_exists=True)

        handle_error = {
            # 250 and 251 are not errors
            550: handle_550,
            551: lambda _: dict(deliverable=False, host_exists=True),
            552: lambda _: dict(deliverable=True, host_exists=True, full_inbox=True),
            553: lambda _: dict(deliverable=False, host_exists=True),
            450: lambda _: dict(deliverable=False, host_exists=True),
            451: lambda _: dict(deliverable=False, message="Local error processing, try again later."),
            452: lambda _: dict(deliverable=True, full_inbox=True),

            521: lambda _: dict(deliverable=False, host_exists=False),
            421: lambda _: dict(deliverable=False, host_exists=True, message="Service not available, try again later."),
            441: lambda _: dict(deliverable=True, full_inbox=True, host_exists=True)
        }

        handle_unrecognised = lambda a: dict(message=f"Unrecognised error: {a}", deliverable=False)

        Address = namedtuple("Address", ["name", "addr", "username", "domain"])

        class EmailVerifier:

            def __init__(self,

                         source_addr,
                         proxy,
                         proxy_type=None,
                         proxy_addr=None,
                         proxy_port=None,
                         proxy_username=None,
                         proxy_password=None):

                self.proxy = proxy
                if proxy_type:
                    try:
                        self.proxy_type = self.proxy[proxy_type.lower()]
                    except KeyError as e:
                        raise UnknownProxyError(proxy_type)
                else:
                    self.proxy_type = None
                self.source_addr = source_addr
                self.proxy_addr = proxy_addr
                self.proxy_port = proxy_port
                self.proxy_username = proxy_username
                self.proxy_password = proxy_password

            def _parse_address(self, email) -> Address:

                name, addr = parseaddr(email)
                if not addr:
                    raise EmailFormatError(f"email does not contain address: {email}")
                try:
                    name = addr.split('@')[:-1][0]
                    domain = addr.split('@')[-1]
                    username = addr.split('@')[:-1][0]
                except IndexError:
                    raise EmailFormatError(f"address provided is invalid: {email}")
                return Address(name, addr, username, domain)

            def _random_email(self, domain):

                return f'{binascii.hexlify(os.urandom(20)).decode()}@{domain}'

            def _can_deliver(self,
                             exchange: str,
                             address: str):

                host_exists = False
                with SMTP(exchange[1],
                          proxy_type=self.proxy_type,
                          proxy_addr=self.proxy_addr,
                          proxy_port=self.proxy_port,
                          proxy_username=self.proxy_username,
                          proxy_password=self.proxy_password) as smtp:
                    host_exists = True
                    smtp.helo()
                    smtp.mail(self.source_addr)
                    test_resp = smtp.rcpt(address.addr)
                    catch_all_resp = smtp.rcpt(self._random_email(address.domain))
                    if test_resp[0] == 250:
                        deliverable = True
                        if catch_all_resp[0] == 250:
                            catch_all = True
                        else:
                            catch_all = False
                    elif test_resp[0] >= 400:
                        raise SMTPRecepientException(*test_resp)
                return host_exists, deliverable, catch_all

            def verify(self, email):

                lookup = {
                    'address': None,
                    'valid_format': False,
                    'deliverable': False,
                    'full_inbox': False,
                    'host_exists': False,
                    'catch_all': False,
                }
                try:
                    lookup['address'] = self._parse_address(email)
                    lookup['valid_format'] = True
                except EmailFormatError:
                    lookup['address'] = f"{email}"
                    return lookup

                try:
                    mx_record = resolver.resolve(lookup['address'].domain, 'MX')
                    mail_exchangers = [exchange.to_text().split() for exchange in mx_record]
                    lookup['host_exists'] = True
                except (resolver.NoAnswer, resolver.NXDOMAIN, resolver.NoNameservers):
                    lookup['host_exists'] = False
                    return lookup

                for exchange in mail_exchangers:
                    try:
                        host_exists, deliverable, catch_all = self._can_deliver(exchange, lookup['address'])
                        if deliverable:
                            lookup['host_exists'] = host_exists
                            lookup['deliverable'] = deliverable
                            lookup['catch_all'] = catch_all
                            break
                    except SMTPRecepientException as err:

                        kwargs = handle_error.get(err.code, handle_unrecognised)(err.response)

                        lookup = {**lookup, **kwargs}

                    except smtplib.SMTPServerDisconnected as err:
                        lookup['message'] = "Internal Error"
                    except smtplib.SMTPConnectError as err:

                        lookup['message'] = "Internal Error. Maybe blacklisted"

                return lookup

        verifier = EmailVerifier(source_addr='user@example.com', proxy=self.proxy)
        email = self.email
        final_return = verifier.verify(email)
        return final_return


