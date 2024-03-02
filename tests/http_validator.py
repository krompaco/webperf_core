# -*- coding: utf-8 -*-
import os
import datetime
import traceback
import urllib.parse
import datetime
import sys
import ssl
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.util import ssl_
# https://docs.python.org/3/library/urllib.parse.html
import urllib
import config
from models import Rating
from tests.utils import dns_lookup
from tests.utils import *
from tests.sitespeed_base import get_result
import dns.name
import dns.query
import dns.dnssec
import dns.message
import dns.resolver
import dns.rdatatype
import datetime
import gettext
_local = gettext.gettext


# DEFAULTS
request_timeout = config.http_request_timeout
useragent = config.useragent
review_show_improvements_only = config.review_show_improvements_only
sitespeed_use_docker = config.sitespeed_use_docker
try:
    software_browser = config.software_browser
except:
    # If browser is not set in config.py this will be the default
    software_browser = 'chrome'
try:
    use_cache = config.cache_when_possible
    cache_time_delta = config.cache_time_delta
except:
    # If cache_when_possible variable is not set in config.py this will be the default
    use_cache = False
    cache_time_delta = timedelta(hours=1)


def run_test(_, langCode, url):
    """
    Only work on a domain-level. Returns tuple with decimal for grade and string with review
    """

    # TODO: Check if we can use sitespeed instead (to make it more accurate), https://addons.mozilla.org/en-US/firefox/addon/http2-indicator/

    result_dict = {}

    language = gettext.translation(
        'http_validator', localedir='locales', languages=[langCode])
    language.install()
    _local = language.gettext

    print(_local('TEXT_RUNNING_TEST'))

    print(_('TEXT_TEST_START').format(
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    # We must take in consideration "www." subdomains...

    orginal_url = url
    o = urllib.parse.urlparse(url)
    hostname = o.hostname

    if hostname.startswith('www.'):
        url = url.replace(hostname, hostname[4:])

    o = urllib.parse.urlparse(url)
    hostname = o.hostname

    result_dict = check_http_to_https(url)

    result_dict = check_tls_version(result_dict)

    result_dict = check_ip_version(result_dict)

    result_dict = check_http_version(url, result_dict)

    result_dict = check_dnssec(hostname, result_dict)

    result_dict = cleanup(result_dict)

    rating = rate(result_dict, _)

    nice_result = json.dumps(result_dict, indent=3)
    print('DEBUG TOTAL', nice_result)

    print(_('TEXT_TEST_END').format(
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    return (rating, result_dict)

def rate(result_dict, _):
    rating = Rating(_, review_show_improvements_only)

    # result_dict = {
    #     'protocols': ['HTTP/1', 'HTTP/1.1', 'HTTP/2', 'HTTP/3', 'DNSSEC'],
    #     'schemes': ['HTTPS', 'HTTP', 'HTTP-REDIRECT', 'HTTPS-REDIRECT', 'HSTS-PRELOAD*'],
    #     'ip-versions': ['IPv6', 'IPv4', 'IPv4*', 'IPv6*'],
    #     'transport-layers': ['TLSv1.3', 'TLSv1.2','TLSv1.1', 'TLSv1.0', 'SSLv3', 'SSLv2']
    # }

    for domain in result_dict.keys():
        if 'HTTP/1.1' in result_dict[domain]['protocols']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, No HTTP/1.1 support'.format(domain))
            rating += sub_rating

        if 'HTTP/2' in result_dict[domain]['protocols']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, No HTTP/2 support'.format(domain))
            rating += sub_rating

        if 'HTTP/3' in result_dict[domain]['protocols']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, No HTTP/3 support'.format(domain))
            rating += sub_rating

        if 'DNSSEC' in result_dict[domain]['features']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_integrity_and_security(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        elif 'DNSSEC-IGNORE' in result_dict[domain]['features']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_integrity_and_security(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_integrity_and_security(1.0, '- {0}, No DNSSEC support'.format(domain))
            sub_rating.set_standards(1.0, '- {0}, No DNSSEC support'.format(domain))
            rating += sub_rating

        if 'HTTPS' in result_dict[domain]['schemes']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_integrity_and_security(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_integrity_and_security(1.0, '- {0}, No HTTPS support'.format(domain))
            sub_rating.set_standards(1.0, '- {0}, No HTTPS support'.format(domain))
            rating += sub_rating

        if 'HTTP-REDIRECT' in result_dict[domain]['schemes'] or 'HTTP-REDIRECT*' in result_dict[domain]['schemes']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_integrity_and_security(1.0, '- {0}, Uses none encrypted redirect'.format(domain))
            rating += sub_rating

        if 'HTTPS-REDIRECT' in result_dict[domain]['schemes'] or 'HTTPS-REDIRECT*' in result_dict[domain]['schemes']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_integrity_and_security(5.0)
            rating += sub_rating

            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)

        if 'HSTS' in result_dict[domain]['features']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)

            if 'INVALIDATE-HSTS' in result_dict[domain]['features']:
                sub_rating.set_overall(1.5)
                sub_rating.set_integrity_and_security(1.5, '- {0}, Is NOT using HSTS because of redirect'.format(domain))
                sub_rating.set_standards(1.5, '- {0}, Is NOT using HSTS because of redirect'.format(domain))
            elif 'HSTS-HEADER-PRELOAD-FOUND' in result_dict[domain]['features'] and ('HSTS-PRELOAD' in result_dict[domain]['features'] or 'HSTS-PRELOAD*' in result_dict[domain]['features']):
                sub_rating.set_integrity_and_security(5.0)
            elif 'HSTS-HEADER-MAXAGE-1YEAR' in result_dict[domain]['features']:
                sub_rating.set_integrity_and_security(4.99, '- {0}, You might want to use "preload" in HSTS'.format(domain))
            elif 'HSTS-HEADER-MAXAGE-TOO-LOW' in result_dict[domain]['features']:
                sub_rating.set_overall(4.5)
                sub_rating.set_integrity_and_security(4.0, '- {0}, max-age used in HSTS is less than 1 year'.format(domain))
            elif 'HSTS-HEADER-MAXAGE-6MONTHS' in result_dict[domain]['features']:
                sub_rating.set_overall(4.0)
                sub_rating.set_integrity_and_security(3.0, '- {0}, max-age used in HSTS is less than 6 months'.format(domain))
            elif 'HSTS-HEADER-MAXAGE-1MONTH' in result_dict[domain]['features']:
                sub_rating.set_overall(3.5)
                sub_rating.set_integrity_and_security(2.0, '- {0}, max-age used in HSTS is less than 1 month'.format(domain))
            else:
                sub_rating.set_overall(3.0)
                sub_rating.set_integrity_and_security(1.0, '- {0}, max-age is missing in HSTS'.format(domain))
            rating += sub_rating
        elif 'HSTS-HEADER-ON-PARENTDOMAIN-FOUND' in result_dict[domain]['features'] and 'INVALIDATE-HSTS' not in result_dict[domain]['features']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(4.99, '- {0}, Only parent HSTS used, child should also use HSTS'.format(domain))
            sub_rating.set_integrity_and_security(4.99, '- {0}, Only parent HSTS used, child should also use HSTS'.format(domain))
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, Is NOT using HSTS'.format(domain))
            sub_rating.set_integrity_and_security(1.0, '- {0}, Is NOT using HSTS'.format(domain))
            rating += sub_rating

        if 'IPv4' in result_dict[domain]['ip-versions'] or 'IPv4*' in result_dict[domain]['ip-versions']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, No IPv4 support'.format(domain))
            rating += sub_rating

        if 'IPv6' in result_dict[domain]['ip-versions'] or 'IPv6*' in result_dict[domain]['ip-versions']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, No IPv6 support'.format(domain))
            rating += sub_rating

        if 'TLSv1.3' in result_dict[domain]['transport-layers']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)
            sub_rating.set_integrity_and_security(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, No support for transport layer: TLSv1.3'.format(domain))
            sub_rating.set_integrity_and_security(1.0, '- {0}, No support for transport layer: TLSv1.3'.format(domain))
            rating += sub_rating

        if 'TLSv1.2' in result_dict[domain]['transport-layers']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_standards(5.0)
            sub_rating.set_integrity_and_security(5.0)
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_standards(1.0, '- {0}, No support for transport layer: TLSv1.2'.format(domain))
            sub_rating.set_integrity_and_security(1.0, '- {0}, No support for transport layer: TLSv1.2'.format(domain))
            rating += sub_rating

        if 'TLSv1.1' in result_dict[domain]['transport-layers']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_integrity_and_security(1.0, '- {0}, Support insecure transport layer: TLSv1.1'.format(domain))
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_integrity_and_security(5.0)
            rating += sub_rating

        if 'TLSv1.0' in result_dict[domain]['transport-layers']:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(1.0)
            sub_rating.set_integrity_and_security(1.0, '- {0}, Support insecure transport layer: TLSv1.0'.format(domain))
            rating += sub_rating
        else:
            sub_rating = Rating(_, review_show_improvements_only)
            sub_rating.set_overall(5.0)
            sub_rating.set_integrity_and_security(5.0)
            rating += sub_rating

    return rating

def cleanup(result_dict):
    for domain in result_dict.keys():
        del result_dict[domain]['urls']
    return result_dict

def merge_dicts(dict1, dict2):
    if dict1 == None:
        return dict2
    if dict2 == None:
        return dict1

    for key, value in dict2.items():
        if key in dict1:
            for subkey, subvalue in value.items():
                dict1[key][subkey].extend(subvalue)
                dict1[key][subkey] = sorted(list(set(dict1[key][subkey])))
        else:
            dict1[key] = value
    return dict1

def rate_url(filename):

    result = {}

    if filename == '':
        return result
    
    # Fix for content having unallowed chars
    with open(filename) as json_input_file:
        har_data = json.load(json_input_file)

        if 'log' in har_data:
            har_data = har_data['log']

        for entry in har_data["entries"]:
            req = entry['request']
            res = entry['response']
            req_url = req['url']

            o = urllib.parse.urlparse(req_url)
            req_domain = o.hostname

            if req_domain not in result:
                result[req_domain] = {
                    'protocols': [],
                    'schemes': [],
                    'ip-versions': [],
                    'transport-layers': [],
                    'features': [],
                    'urls': []
                }

            result[req_domain]['schemes'].append(o.scheme.upper())
            result[req_domain]['urls'].append(req_url)

            if 'httpVersion' in req and req['httpVersion'] != '':
                result[req_domain]['protocols'].append(req['httpVersion'].replace('h2', 'HTTP/2').replace('h3', 'HTTP/3').upper())

            if 'httpVersion' in res and res['httpVersion'] != '':
                result[req_domain]['protocols'].append(res['httpVersion'].replace('h2', 'HTTP/2').replace('h3', 'HTTP/3').upper())

            if 'serverIPAddress' in entry:
                if ':' in entry['serverIPAddress']:
                    result[req_domain]['ip-versions'].append('IPv6')
                else:
                    result[req_domain]['ip-versions'].append('IPv4')

            for header in res['headers']:
                if 'name' not in header:
                    continue

                if 'value' not in header:
                    continue

                name = header['name'].lower()
                value = header['value'].strip()

                if 'HSTS' not in result[req_domain]['features'] and 'strict-transport-security' in name:
                    sections = header['value'].split(';')
                    for section in sections:
                        section = section.strip()

                        pair = section.split('=')

                        name = pair[0]
                        value = None
                        if len(pair) == 2:
                            value = pair[1]

                        if 'max-age' == name:
                            result[req_domain]['features'].append('HSTS-HEADER-MAXAGE-FOUND')
                            try:
                                maxage = int(value)
                                # 1 month =   2628000
                                # 6 month =  15768000
                                # check if maxage is more then 1 year
                                if maxage >= 31536000:
                                    result[req_domain]['features'].append('HSTS-HEADER-MAXAGE-1YEAR')
                                elif maxage < 2628000:
                                    result[req_domain]['features'].append('HSTS-HEADER-MAXAGE-1MONTH')
                                elif maxage < 15768000:
                                    result[req_domain]['features'].append('HSTS-HEADER-MAXAGE-6MONTHS')
                                else:
                                    result[req_domain]['features'].append('HSTS-HEADER-MAXAGE-TOO-LOW')

                                result[req_domain]['features'].append('HSTS')
                            except:
                                a = 1
                        elif 'includeSubDomains' == name:
                            result[req_domain]['features'].append('HSTS-HEADER-SUBDOMAINS-FOUND')
                        elif 'preload' == name:
                            result[req_domain]['features'].append('HSTS-HEADER-PRELOAD-FOUND')
                elif 'location' in name:
                    if value.startswith('https://{0}'.format(req_domain)):
                        result[req_domain]['schemes'].append('HTTPS-REDIRECT')
                    elif value.startswith('https://'):
                        result[req_domain]['schemes'].append('HTTPS-REDIRECT-OTHERDOMAIN')
                        result[req_domain]['features'].append('INVALIDATE-HSTS')
                    elif value.startswith('http://{0}'.format(req_domain)):
                        result[req_domain]['schemes'].append('HTTP-REDIRECT')
                        result[req_domain]['features'].append('INVALIDATE-HSTS')
                    elif value.startswith('http://'):
                        result[req_domain]['schemes'].append('HTTP-REDIRECT-OTHERDOMAIN')
                        result[req_domain]['features'].append('INVALIDATE-HSTS')

                    # result[req_domain]['features'].append('LOCATION:{0}'.format(value))



            result[req_domain]['protocols'] = list(set(result[req_domain]['protocols']))
            result[req_domain]['schemes'] = list(set(result[req_domain]['schemes']))
            result[req_domain]['ip-versions'] = list(set(result[req_domain]['ip-versions']))

    return result


def validate_dnssec(domain):
    subdomain = 'static.internetstiftelsen.se'
    domain = 'internetstiftelsen.se'
    print('validate_dnssec', domain)
    # Get the DNSKEY for the domain
    dnskey_answer = dns.resolver.resolve(domain, dns.rdatatype.DNSKEY)
    
    print('\t1')

    # Get the DS for the domain
    ds_answer = dns.resolver.resolve(subdomain, dns.rdatatype.DS)

    print('\t2')

    # Validate the DNSKEY with the DS
    try:
        dns.dnssec.validate(dnskey_answer, ds_answer)
        print("DNSSEC validation passed")
    except dns.dnssec.ValidationFailure:
        print("DNSSEC validation failed")

    print('\t3')

def check_dnssec(hostname, result_dict):
    print('DNSSEC')

    # NOTE: https://www.cloudflare.com/dns/dnssec/how-dnssec-works/
    # NOTE: https://github.com/dnsviz/dnsviz/blob/master/dnsviz/resolver.py
    
    # TODO: DNSSEC (BUT NOT ON ALL NAMESERVERS: internetstiftelsen.se)

    # To facilitate signature validation, DNSSEC adds a few new DNS record types4:

    # RRSIG - Contains a cryptographic signature
    # DNSKEY - Contains a public signing key
    # DS - Contains the hash of a DNSKEY record
    # NSEC and NSEC3 - For explicit denial-of-existence of a DNS record
    # CDNSKEY and CDS - For a child zone requesting updates to DS record(s) in the parent zone
    # get nameservers for target domain




    import dns.zone

    new_entries = list()
    for domainA in result_dict.keys():
        try:
            domain = domainA
            domain_entry = result_dict[domain]

            if hostname != domain:
                domain_entry['features'].append('DNSSEC-IGNORE')
                continue

            # validate_dnssec(domain)
            print('# {0}'.format(domain))

            # if 'svanalytics.piwik.pro' == domainA:
            #     domain = 'piwik.pro'
            #     domain_entry = {
            #         'name': domain,
            #         'protocols': [],
            #         'schemes': [],
            #         'ip-versions': [],
            #         'transport-layers': [],
            #         'features': [],
            #         'urls': []
            #     }
            #     new_entries.append(domain_entry)
            # domain_entry = result_dict[domain]

            dnskey = dns_lookup(domain, dns.rdatatype.DNSKEY)
            # print('\t\tDNSKEY', dnskey)
            print('\tDNSKEY(S):', len(dnskey))
            if len(dnskey) == 0:
                domain_entry['features'].append('DNSSEC-NO-DNSKEY')
            else:
                domain_entry['features'].append('DNSSEC-DNSKEY')

            response = dns.resolver.query('{0}.'.format(domain), dns.rdatatype.NS)
            nsnames = dns_lookup('{0}.'.format(domain), dns.rdatatype.NS)
            print('\tNAMESERVER(S):', len(nsnames))

            # we'll use the first nameserver in this example
            # nof_nsnames = len(response.rrset)
            #nsnames = list()
            for nsname in nsnames:
                #nsnames.append(entry.to_text())

                # print('A', nsnames)
                # nsname = entry.to_text()  # name
                #nsname = response.rrset[1].to_text()  # name
                print('\tA', nsname)

                # test = dns_lookup(domain, dns.rdatatype.RRSIG)
                # print('\t\tRRSIG', test)


                # get DNSKEY for zone
                #request = dns.message.make_query('{0}.'.format(domain), dns.rdatatype.DNSKEY, want_dnssec=True)
                request = dns.message.make_query(domain, dns.rdatatype.DNSKEY, want_dnssec=True)
                # request = dns.message.make_query(domain, dns.rdatatype.DNSKEY)
                # name = dns.name.from_text('{0}.'.format(domain))
                name = dns.name.from_text(domain)
                print('\t\tA.1', name)
                # print('\t\tA.1.1', domain_entry)


                if 'IPv4' in domain_entry['ip-versions'] or 'IPv4*' in domain_entry['ip-versions']:
                    # print('\t\tA.2')
                    response = dns.resolver.query(nsname, dns.rdatatype.A)
                    print('\t\tA.3', response)
                    nsaddr = response.rrset[0].to_text()  # IPv4

                    print('\t\tA.4', nsaddr)

                    # send the query
                    response = dns.query.udp(request, nsaddr)
                    # response = dns.query.udp(request, '8.8.8.8')

                    # print('\t\tA.5', response)
                    print('\t\tA.5')

                    if response.rcode() != 0:
                        # HANDLE QUERY FAILED (SERVER ERROR OR NO DNSKEY RECORD)
                        a = 1
                        print('\t\tD.1', response.rcode())
                        domain_entry['features'].append('DNSSEC-NO-RCODE:{0}'.format(nsname))
                        continue
                    else:
                        a = 2
                        print('\t\tD.2', response.rcode())
                        domain_entry['features'].append('DNSSEC-RCODE:{0}'.format(nsname))

                    # answer should contain two RRSET: DNSKEY and RRSIG (DNSKEY)
                    # answer = response.answer
                    dnskey = None
                    rrsig = None

                    # print('E', answer)
                    if len(response.answer) < 2:
                        # SOMETHING WENT WRONG
                        print('\t\tE.1', len(response.answer))

                        # find the associated RRSIG RRset
                        rrsig = None

                        print('\t\t\tQ.answer', response.answer)
                        print('\t\t\tQ.authority', response.authority)
                        print('\t\t\tQ.additional', response.additional)

                        for rrset in response.answer + response.authority + response.additional:
                            print('\t\tE.2', rrset)
                            if rrset.rdtype == dns.rdatatype.RRSIG:
                                rrsig = rrset
                                break


                        domain_entry['features'].append('DNSSEC-NO-ANSWER:{0}'.format(nsname))
                        continue
                    else:
                        print('\t\tE.2', len(response.answer))

                        # find DNSKEY and RRSIG in answer
                        dnskey = None
                        rrsig = None
                        for rrset in response.answer:
                            if rrset.rdtype == dns.rdatatype.DNSKEY:
                                dnskey = rrset
                            elif rrset.rdtype == dns.rdatatype.RRSIG:
                                rrsig = rrset
                        domain_entry['features'].append('DNSSEC-ANSWER:{0}'.format(nsname))

                        # # validate the answer
                        # if rrsig is not None:                        

                    # the DNSKEY should be self-signed, validate it
                    try:
                        # print('F')
                        # dns.dnssec.validate(answer[0], answer[1], {name: answer[0]})

                        print('\t\tF.1', dnskey)
                        print('\t\tF.2', rrsig)


                        # dns.dnssec.validate(answer, rrsig)
                        dns.dnssec.validate(dnskey, rrsig, {name: dnskey})
                        print('\t\tG.1\r\n')
                    except dns.dnssec.ValidationFailure as vf:
                        # BE SUSPICIOUS
                        a = False
                        # print('G VALIDATION FAIL')
                        print('DNSSEC VALIDATION FAIL', vf)
                        domain_entry['features'].append('DNSSEC-FALIED-VALIDATION:{0}'.format(nsname))
                        print('\t\tG.2 - VALIDATION FAIL\r\n')
                    else:
                        # WE'RE GOOD, THERE'S A VALID DNSSEC SELF-SIGNED KEY FOR example.com
                        # print('G VALIDATION SUCCESS')
                        domain_entry['features'].append('DNSSEC')
                        domain_entry['features'].append('DNSSEC:{0}'.format(nsname))
                        print('\t\tG.3 - VALIDATION SUCCESS\r\n')
                        
                        # a = True

            # if 'IPv6' in result_dict[domain]['ip-versions'] or 'IPv6*' in result_dict[domain]['ip-versions']:
            #     b = 1
            #     print('B IPv6')
        except Exception as e:
            print('DNSSEC EXCEPTION', e)
            with open('failures.log', 'a') as outfile:
                
                outfile.writelines(['###############################################',
                                    '\n# Information:',
                                    '\nDateTime: {0}' .format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                    '\n###############################################'
                                    '\n# Configuration (from config.py):',
                                    '\nuseragent: {0}'.format(config.useragent),
                                    '\nhttp_request_timeout: {0}'.format(config.http_request_timeout),
                                    '\nwebbkoll_sleep: {0}'.format(config.webbkoll_sleep),
                                    '\ncss_review_group_errors: {0}'.format(config.css_review_group_errors),
                                    '\nreview_show_improvements_only: {0}'.format(config.review_show_improvements_only),
                                    '\nylt_use_api: {0}'.format(config.ylt_use_api),
                                    '\nlighthouse_use_api: {0}'.format(config.lighthouse_use_api),
                                    '\nsitespeed_use_docker: {0}'.format(config.sitespeed_use_docker),
                                    '\nsitespeed_iterations: {0}'.format(config.sitespeed_iterations),
                                    '\nlocales: {0}'.format(config.locales),
                                    '\ncache_when_possible: {0}'.format(config.cache_when_possible),
                                    '\ncache_time_delta: {0}'.format(config.cache_time_delta),
                                    '\nsoftware_use_stealth: {0}'.format(config.software_use_stealth),
                                    '\nsoftware_use_detailed_report: {0}'.format(config.software_use_detailed_report),
                                    '\nsoftware_browser: {0}'.format(config.software_browser),
                                    '\n###############################################\n'
                                    ])
                
                
                outfile.writelines(traceback.format_exception(e,e, e.__traceback__))

                outfile.writelines(['###############################################\n\n'])
            c = 1

    for entry in new_entries:
        name = entry['name']
        del entry['name']
        result_dict[name] = entry
        
    return result_dict

def check_http_to_https(url):
    # Firefox
    # dom.security.https_only_mode

    http_url = ''

    o = urllib.parse.urlparse(url)
    o_domain = o.hostname

    if (o.scheme == 'https'):
        http_url = url.replace('https://', 'http://')
    else:
        http_url = url

    browser = 'firefox'
    configuration = ''
    print('HTTP2HTTPS')
    result_dict = get_website_support_from_sitespeed(http_url, configuration, browser, request_timeout)

    # If website redirects to www. domain without first redirecting to HTTPS, make sure we test it.
    if o_domain in result_dict:
        if 'HTTPS' not in result_dict[o_domain]['schemes']:
            result_dict[o_domain]['schemes'].append('HTTP-REDIRECT*')
            https_url = url.replace('http://', 'https://')
            result_dict = merge_dicts(get_website_support_from_sitespeed(https_url, configuration, browser, request_timeout), result_dict)
        else:
            result_dict[o_domain]['schemes'].append('HTTPS-REDIRECT*')

        # TODO: Should we add check for HSTS and if website is in preload list (example: start.stockholm)
        # being in preload list means http:// requests will be converted to https:// request before leaving browser.
        # preload list source can be collected here: https://source.chromium.org/chromium/chromium/src/+/main:net/http/transport_security_state_static.json
        # or is below good enough?
        if 'HTTP' not in result_dict[o_domain]['schemes']:
            result_dict[o_domain]['features'].append('HSTS-PRELOAD*')

    # If we have www. domain, ensure we validate HTTP2HTTPS on that as well
    www_domain_key = 'www.{0}'.format(o_domain)
    if www_domain_key in result_dict:
        if 'HTTP' not in result_dict[www_domain_key]['schemes']:
            result_dict[www_domain_key]['schemes'].append('HTTPS-REDIRECT*')
            www_http_url = http_url.replace(o_domain, www_domain_key)
            result_dict = merge_dicts(get_website_support_from_sitespeed(www_http_url, configuration, browser, request_timeout), result_dict)
        else:
            result_dict[www_domain_key]['schemes'].append('HTTP-REDIRECT*')


    domains = list(result_dict.keys())
    hsts_domains = list()
    for domain in domains:
        if 'HSTS-HEADER-SUBDOMAINS-FOUND' in result_dict[domain]['features'] and 'HSTS' in result_dict[domain]['features']:
            hsts_domains.append(domain)

    for hsts_domain in hsts_domains:
        for domain in domains:
            if domain.endswith('.{0}'.format(hsts_domain)):
                result_dict[domain]['features'].append('HSTS-HEADER-ON-PARENTDOMAIN-FOUND')
            

        #     webperf.se
        # cdn.webperf.se
            



    return result_dict


def check_ip_version(result_dict):
    # network.dns.ipv4OnlyDomains
    # network.dns.disableIPv6

    if not contains_value_for_all(result_dict, 'ip-versions', 'IPv4'):
        for domain in result_dict.keys():
            if 'IPv4' not in result_dict[domain]['ip-versions']:
                ip4_result = dns_lookup(domain, "A")
                if len(ip4_result) > 0:
                    result_dict[domain]['ip-versions'].append('IPv4*')

    if not contains_value_for_all(result_dict, 'ip-versions', 'IPv6'):
        for domain in result_dict.keys():
            if 'IPv6' not in result_dict[domain]['ip-versions']:
                ip4_result = dns_lookup(domain, "AAAA")
                if len(ip4_result) > 0:
                    result_dict[domain]['ip-versions'].append('IPv6*')

    return result_dict


def protocol_version_score(url, domain, protocol_version, result_dict):
    protocol_rule = False
    protocol_name = ''

    try:
        if protocol_version == ssl.PROTOCOL_TLS:
            protocol_name = 'TLSv1.3'
            assert ssl.HAS_TLSv1_3
            protocol_rule = ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2
        elif protocol_version == ssl.PROTOCOL_TLSv1_2:
            protocol_name = 'TLSv1.2'
            assert ssl.HAS_TLSv1_2
            protocol_rule = ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3
        elif protocol_version == ssl.PROTOCOL_TLSv1_1:
            protocol_name = 'TLSv1.1'
            assert ssl.HAS_TLSv1_1
            protocol_rule = ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_2 | ssl.OP_NO_TLSv1_3
        elif protocol_version == ssl.PROTOCOL_TLSv1:
            protocol_name = 'TLSv1.0'
            assert ssl.HAS_TLSv1
            protocol_rule = ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2 | ssl.OP_NO_TLSv1_3
        elif protocol_version == ssl.PROTOCOL_SSLv3:
            protocol_name = 'SSLv3'
            assert ssl.HAS_SSLv3
            protocol_rule = ssl.OP_NO_SSLv2 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2 | ssl.OP_NO_TLSv1_3
        elif protocol_version == ssl.PROTOCOL_SSLv2:
            protocol_name = 'SSLv2'
            protocol_rule = ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2 | ssl.OP_NO_TLSv1_3
            assert ssl.HAS_SSLv2

        if has_protocol_version(
            url, True, protocol_rule)[0]:
            result_dict[domain]['transport-layers'].append(protocol_name)
        elif has_protocol_version(
            url, False, protocol_rule)[0]:
            result_dict[domain]['transport-layers'].append('{0}-'.format(protocol_name))

    except ssl.SSLError as sslex:
        print('error 0.0s', sslex)
        pass
    except AssertionError:
        print('### No {0} support on your machine, unable to test ###'.format(
            protocol_name))
        pass
    except:
        print('error protocol_version_score: {0}'.format(sys.exc_info()[0]))
        pass

    return result_dict


def check_tls_version(result_dict):
    for domain in result_dict.keys():
        # TODO: Make sure to find https:// based url instead of creating one.
        https_url = result_dict[domain]['urls'][0].replace('http://', 'https://')
        result_dict = protocol_version_score(https_url, domain, ssl.PROTOCOL_TLS, result_dict)
        result_dict = protocol_version_score(https_url, domain, ssl.PROTOCOL_TLSv1_2, result_dict)
        result_dict = protocol_version_score(https_url, domain, ssl.PROTOCOL_TLSv1_1, result_dict)
        result_dict = protocol_version_score(https_url, domain, ssl.PROTOCOL_TLSv1, result_dict)

    # Firefox:
    # security.tls.version.min
    # security.tls.version.max

    # 1 = TLS 1.0
    # 2 = TLS 1.1
    # 3 = TLS 1.2
    # 4 = TLS 1.3

    # o = urllib.parse.urlparse(url)
    # domain = o.hostname

    # url = url.replace('http://', 'https://')

    # browser = 'firefox'
    # # configuration = ' --firefox.preference network.http.http2.enabled:false --firefox.preference network.http.http3.enable:false --firefox.preference network.http.version:1.1'
    # configuration = ' --firefox.preference security.tls.version.min:4 --firefox.preference security.tls.version.max:4'
    # url2 = change_url_to_test_url(url, 'TLS1_3')
    # print('TLS/1.3')
    # tls1_3_result = get_website_support_from_sitespeed(url2, configuration, browser, 2 * 60)
    # for domain in tls1_3_result.keys():
    #     result_dict[domain]['transport-layers'].append('TLSv1.3')

    # configuration = ' --firefox.preference security.tls.version.min:3 --firefox.preference security.tls.version.max:3'
    # url2 = change_url_to_test_url(url, 'TLS1_2')
    # print('TLS/1.2')
    # tls1_2_result = get_website_support_from_sitespeed(url2, configuration, browser, 2 * 60)
    # for domain in tls1_2_result.keys():
    #     result_dict[domain]['transport-layers'].append('TLSv1.2')

    # configuration = ' --firefox.preference security.tls.version.min:2 --firefox.preference security.tls.version.max:2'
    # url2 = change_url_to_test_url(url, 'TLS1_1')
    # print('TLS/1.1')
    # tls1_1_result = get_website_support_from_sitespeed(url2, configuration, browser, 2 * 60)
    # for domain in tls1_1_result.keys():
    #     result_dict[domain]['transport-layers'].append('TLSv1.1')

    # configuration = ' --firefox.preference security.tls.version.min:1 --firefox.preference security.tls.version.max:1'
    # url2 = change_url_to_test_url(url, 'TLS1_0')
    # print('TLS/1.0')
    # tls1_0_result = get_website_support_from_sitespeed(url2, configuration, browser, 2 * 60)
    # for domain in tls1_0_result.keys():
    #     result_dict[domain]['transport-layers'].append('TLSv1.0')

    # TODO: check cipher security
    # TODO: re add support for identify wrong certificate

    return result_dict

def get_website_support_from_sitespeed(url, configuration, browser, timeout):
    # We don't need extra iterations for what we are using it for
    sitespeed_iterations = 1
    sitespeed_arg = '--plugins.remove screenshot --plugins.remove html --plugins.remove metrics --browsertime.screenshot false --screenshot false --screenshotLCP false --browsertime.screenshotLCP false --videoParams.createFilmstrip false --visualMetrics false --visualMetricsPerceptual false --visualMetricsContentful false --browsertime.headless true --utc true -n {0}'.format(
        sitespeed_iterations)

    if 'firefox' in browser:
        sitespeed_arg = '-b firefox --firefox.includeResponseBodies all --firefox.preference privacy.trackingprotection.enabled:false --firefox.preference privacy.donottrackheader.enabled:false --firefox.preference browser.safebrowsing.malware.enabled:false --firefox.preference browser.safebrowsing.phishing.enabled:false{1} {0}'.format(
            sitespeed_arg, configuration)
    else:
        sitespeed_arg = '-b chrome --chrome.cdp.performance false --browsertime.chrome.timeline false --browsertime.chrome.includeResponseBodies all --browsertime.chrome.args ignore-certificate-errors {0}'.format(
            sitespeed_arg)

    sitespeed_arg = '--shm-size=1g {0}'.format(
        sitespeed_arg)

    if 'nt' not in os.name:
        sitespeed_arg += ' --xvfb'

    (result_folder_name, filename) = get_result(
        url, sitespeed_use_docker, sitespeed_arg, timeout)
    
    result = rate_url(filename)

    # nice_result = json.dumps(result, indent=3)
    # print('DEBUG', nice_result)

    return result

def contains_value_for_all(result_dict, key, value):
    if result_dict == None:
        return False

    has_value = True    
    for domain in result_dict.keys():
        if key not in result_dict[domain] or value not in result_dict[domain][key]:
            has_value = False
    return has_value

def check_http_version(url, result_dict):

    # SiteSpeed (firefox):
    # "httpVersion": "HTTP/1"
    # "httpVersion": "HTTP/1.1"
    # "httpVersion": "HTTP/2"
    # "httpVersion": "HTTP/3"

    # SiteSpeed (chrome):
    # "httpVersion": "http/1.1"
    # "httpVersion": "h2"
    # "httpVersion": "h3"

    # Chrome:
    # https://www.chromium.org/for-testers/providing-network-details/


    # Firefox:
    # about:networking
    # network.http.http2.enabled
    # network.http.http3.enable
    # network.http.version

    # network.http.version and their effects1:
    # - 0.9
    # - 1.0
    # - 1.1 (Default)
    # - 2.0
    # - 3.02

    # Response Header: alt-svc
    # h3=\":443\"; ma=2592000, h3-29=\":443\"; ma=2592000, h3-Q050=\":443\"; ma=2592000, h3-Q046=\":443\"; ma=2592000, h3-Q043=\":443\"; ma=2592000, quic=\":443\"; ma=2592000; v=\"43,46\"
    # h3=":443";
    # ma=2592000, h3-29=":443";
    # ma=2592000, h3-Q050=":443";
    # ma=2592000, h3-Q046=":443";
    # ma=2592000, h3-Q043=":443";
    # ma=2592000, quic=":443";
    # ma=2592000; v="43,46"

    # https://www.http3check.net/?host=https%3A%2F%2Fwebperf.se
    # 0-RTT
    # H3
    # H3-29
    # H3-Q050
    # H3-Q046
    # H3-Q043
    # Q043
    # Q046

    if not contains_value_for_all(result_dict, 'protocols', 'HTTP/1.1'):
        browser = 'firefox'
        # configuration = ' --firefox.preference network.http.http2.enabled:false --firefox.preference network.http.http3.enable:false --firefox.preference network.http.version:1.1'
        configuration = ' --firefox.preference network.http.http2.enabled:false --firefox.preference network.http.http3.enable:false'
        url2 = change_url_to_test_url(url, 'HTTPv1')
        print('HTTP/1.1')
        result_dict = merge_dicts(get_website_support_from_sitespeed(url2, configuration, browser, request_timeout), result_dict)

    if not contains_value_for_all(result_dict, 'protocols', 'HTTP/2'):
        browser = 'firefox'
        configuration = ' --firefox.preference network.http.http2.enabled:true --firefox.preference network.http.http3.enable:false --firefox.preference network.http.version:3.0'
        url2 = change_url_to_test_url(url, 'HTTPv2')
        print('HTTP/2')
        result_dict = merge_dicts(get_website_support_from_sitespeed(url2, configuration, browser, request_timeout), result_dict)

    if not contains_value_for_all(result_dict, 'protocols', 'HTTP/3'):
        browser = 'firefox'
        configuration = ' --firefox.preference network.http.http2.enabled:false --firefox.preference network.http.http3.enable:true --firefox.preference network.http.version:3.0'
        url2 = change_url_to_test_url(url, 'HTTPv3')
        print('HTTP/3')
        result_dict = merge_dicts(get_website_support_from_sitespeed(url2, configuration, browser, request_timeout), result_dict)

    return result_dict

# Read post at: https://hussainaliakbar.github.io/restricting-tls-version-and-cipher-suites-in-python-requests-and-testing-wireshark/
WEAK_CIPHERS = (
    'ECDHE+AES128+CBC+SHA:'
    'ECDHE+AES256+CBC+SHA:'
    'ECDHE+RSA+3DES+EDE+CBC+SHA:'
    'ECDHE+RSA+AES256+GCM+SHA383:'
    'RSA+AES128+CBC+SHA:'
    'RSA+AES256+CBC+SHA:'
    'RSA+AES128+GCM+SHA256:'
    'RSA+AES256+GCM+SHA:'
    'RSA+AES256+GCM+SHA383:'
    'RSA+CAMELLIA128+CBC+SHA:'
    'RSA+CAMELLIA256+CBC+SHA:'
    'RSA+IDEA+CBC+SHA:'
    'RSA+AES256+GCM+SHA:'
    'RSA+3DES+EDE+CBC+SHA:'
    'RSA+SEED+CBC+SHA:'
    'DHE+RSA+3DES+EDE+CBC+SHA:'
    'DHE+RSA+AES128+CBC+SHA:'
    'DHE+RSA+AES256+CBC+SHA:'
    'DHE+RSA+CAMELLIA128+CBC+SHA:'
    'DHE+RSA+CAMELLIA256+CBC+SHA:'
    'DHE+RSA+SEED+CBC+SHA:'
)


class TlsAdapterWeakCiphers(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapterWeakCiphers, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(
            ciphers=WEAK_CIPHERS,
            cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)

        self.poolmanager = PoolManager(*pool_args,
                                       ssl_context=ctx,
                                       **pool_kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = ssl_.create_urllib3_context(ciphers=WEAK_CIPHERS)
        kwargs['ssl_context'] = context
        return super(TlsAdapterWeakCiphers, self).proxy_manager_for(*args, **kwargs)


def has_weak_cipher(url, protocol_version):
    session = False

    try:
        # print('ssl._DEFAULT_CIPHERS', ssl._DEFAULT_CIPHERS)

        session = requests.session()
        adapter = TlsAdapterWeakCiphers(protocol_version)

        session.mount(url, adapter)

    except ssl.SSLError as sslex:
        # print('### No weak cipher support on your machine, unable to test: {0} ###'.format(
        #    WEAK_CIPHERS))
        return (False, 'weak_cipher SSLError {0}'.format(sslex))

    try:
        allow_redirects = False

        headers = {'user-agent': useragent}
        a = session.get(url, verify=False, allow_redirects=allow_redirects,
                        headers=headers, timeout=request_timeout)

        if a.status_code == 200 or a.status_code == 301 or a.status_code == 302 or a.status_code == 404:
            # print('is ok')
            return (True, 'is ok')

        resulted_in_html = '<html' in a.text

        # if resulted_in_html:
        #    print('has html')
        # else:
        #    print('no html')
        return (resulted_in_html, 'has <html tag in result')
    except ssl.SSLCertVerificationError as sslcertex:
        # print('weak_cipher SSLCertVerificationError', sslcertex)
        return (True, 'weak_cipher SSLCertVerificationError: {0}'.format(sslcertex))
    except ssl.SSLError as sslex:
        # print('error has_weak_cipher SSLError1', sslex)
        return (False, 'weak_cipher SSLError {0}'.format(sslex))
    except ConnectionResetError as resetex:
        # print('error ConnectionResetError', resetex)
        return (False, 'weak_cipher ConnectionResetError {0}'.format(resetex))
    except requests.exceptions.SSLError as sslerror:
        # print('error weak_cipher SSLError2', sslerror)
        return (False, 'Unable to verify: SSL error occured')
    except requests.exceptions.ConnectionError as conex:
        # print('error weak_cipher ConnectionError', conex)
        return (False, 'Unable to verify: connection error occured')
    except Exception as exception:
        # print('weak_cipher test', exception)
        return (False, 'weak_cipher Exception {0}'.format(exception))


# Read post at: https://hussainaliakbar.github.io/restricting-tls-version-and-cipher-suites-in-python-requests-and-testing-wireshark/
INSECURE_CIPHERS = (
    'RSA+RC4+MD5:'
    'RSA+RC4128+MD5:'
    'RSA+RC4+SHA:'
    'RSA+RC4128+SHA:'
    'ECDHE+RSA+RC4+SHA:'
    'ECDHE+RSA+RC4+SHA:'
    'ECDHE+RSA+RC4128+MD5:'
    'ECDHE+RSA+RC4128+MD5:'
)


class TlsAdapterInsecureCiphers(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapterInsecureCiphers, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(
            ciphers=INSECURE_CIPHERS,
            cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)

        self.poolmanager = PoolManager(*pool_args,
                                       ssl_context=ctx,
                                       **pool_kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = ssl_.create_urllib3_context(ciphers=INSECURE_CIPHERS)
        kwargs['ssl_context'] = context
        return super(TlsAdapterInsecureCiphers, self).proxy_manager_for(*args, **kwargs)


def has_insecure_cipher(url, protocol_version):
    session = False

    try:
        # print('ssl._DEFAULT_CIPHERS', ssl._DEFAULT_CIPHERS)

        session = requests.session()
        adapter = TlsAdapterInsecureCiphers(protocol_version)

        session.mount(url, adapter)

    except ssl.SSLError as sslex:
        # print('### No weak cipher support on your machine, unable to test: {0} ###'.format(
        #    WEAK_CIPHERS))
        return (False, 'insecure_cipher SSLError {0}'.format(sslex))

    try:
        allow_redirects = False

        headers = {'user-agent': useragent}
        a = session.get(url, verify=False, allow_redirects=allow_redirects,
                        headers=headers, timeout=request_timeout)

        if a.status_code == 200 or a.status_code == 301 or a.status_code == 302 or a.status_code == 404:
            # print('is ok')
            return (True, 'is ok')

        resulted_in_html = '<html' in a.text

        # if resulted_in_html:
        #    print('has html')
        # else:
        #    print('no html')
        return (resulted_in_html, 'has <html tag in result')
    except ssl.SSLCertVerificationError as sslcertex:
        # print('weak_cipher SSLCertVerificationError', sslcertex)
        return (True, 'insecure_cipher SSLCertVerificationError: {0}'.format(sslcertex))
    except ssl.SSLError as sslex:
        # print('error has_weak_cipher SSLError1', sslex)
        return (False, 'insecure_cipher SSLError {0}'.format(sslex))
    except ConnectionResetError as resetex:
        # print('error ConnectionResetError', resetex)
        return (False, 'insecure_cipher ConnectionResetError {0}'.format(resetex))
    except requests.exceptions.SSLError as sslerror:
        # print('error weak_cipher SSLError2', sslerror)
        return (False, 'Unable to verify: SSL error occured')
    except requests.exceptions.ConnectionError as conex:
        # print('error weak_cipher ConnectionError', conex)
        return (False, 'Unable to verify: connection error occured')
    except Exception as exception:
        # print('weak_cipher test', exception)
        return (False, 'insecure_cipher Exception {0}'.format(exception))


class TlsAdapterCertRequired(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapterCertRequired, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(
            cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)

        self.poolmanager = PoolManager(*pool_args,
                                       ssl_context=ctx,
                                       **pool_kwargs)


class TlsAdapterNoCert(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapterNoCert, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(
            cert_reqs=ssl.CERT_NONE,
            options=self.ssl_options)

        self.poolmanager = PoolManager(*pool_args,
                                       ssl_context=ctx,
                                       **pool_kwargs)


def has_protocol_version(url, validate_hostname, protocol_version):
    session = requests.session()
    if validate_hostname:
        adapter = TlsAdapterCertRequired(protocol_version)
    else:
        adapter = TlsAdapterNoCert(protocol_version)

    session.mount("https://", adapter)

    try:
        allow_redirects = False

        headers = {'user-agent': useragent}
        session.get(url, verify=validate_hostname, allow_redirects=allow_redirects,
                        headers=headers, timeout=request_timeout)

        return (True, 'is ok')

    except ssl.SSLCertVerificationError as sslcertex:
        # print('protocol version SSLCertVerificationError', sslcertex)
        if validate_hostname:
            return (True, 'protocol version SSLCertVerificationError: {0}'.format(sslcertex))
        else:
            return (False, 'protocol version SSLCertVerificationError: {0}'.format(sslcertex))
    except ssl.SSLError as sslex:
        # print('protocol version SSLError', sslex)
        return (False, 'protocol version SSLError: {0}'.format(sslex))
    except ssl.SSLCertVerificationError as sslcertex:
        # print('protocol version SSLCertVerificationError', sslcertex)
        return (True, 'protocol version SSLCertVerificationError: {0}'.format(sslcertex))
    except ssl.SSLError as sslex:
        # print('error protocol version ', sslex)
        return (False, 'protocol version SSLError {0}'.format(sslex))
    except ConnectionResetError as resetex:
        # print('error protocol version  ConnectionResetError', resetex)
        return (False, 'protocol version  ConnectionResetError {0}'.format(resetex))
    except requests.exceptions.SSLError as sslerror:
        # print('error protocol version  SSLError', sslerror)
        return (False, 'Unable to verify: SSL error occured')
    except requests.exceptions.ConnectionError as conex:
        # print('error protocol version  ConnectionError', conex)
        return (False, 'Unable to verify: connection error occured')
    except Exception as exception:
        # print('protocol version  test', exception)
        return (False, 'protocol version  Exception {0}'.format(exception))
