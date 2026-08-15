#!/usr/bin/env python3
"""
RouterOS Address List Generator for GitHub and Global-ForWork (Cloudflare, Akamai, CloudFront, Fastly, Google, Google Cloud, GitHub).
"""

import sys
import json
import urllib.request
import urllib.error
import ipaddress
import argparse
import time

USER_AGENT = "Mozilla/5.0 (compatible; RouterOS-IPList-Bot/1.0)"

def fetch_json(url, retries=3, delay=2):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except Exception as e:
            print(f"[WARN] Fetching {url} failed (attempt {attempt}/{retries}): {e}", file=sys.stderr)
            if attempt < retries:
                time.sleep(delay * attempt)
            else:
                print(f"[ERROR] Failed to fetch {url} after {retries} attempts.", file=sys.stderr)
                raise

def parse_ipv4_network(cidr_str):
    if not isinstance(cidr_str, str):
        return None
    cidr_str = cidr_str.strip()
    if not cidr_str or ":" in cidr_str:
        return None
    try:
        net = ipaddress.ip_network(cidr_str, strict=False)
        if isinstance(net, ipaddress.IPv4Network):
            return net
    except ValueError:
        pass
    return None

def get_github_ips():
    print("[INFO] Fetching GitHub IP ranges...")
    url = "https://api.github.com/meta"
    data = fetch_json(url)
    networks = set()
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                net = parse_ipv4_network(item)
                if net:
                    networks.add(net)
    print(f"[INFO] Found {len(networks)} GitHub IPv4 subnets.")
    return networks

def get_cloudflare_ips():
    print("[INFO] Fetching Cloudflare IP ranges...")
    url = "https://api.cloudflare.com/client/v4/ips"
    data = fetch_json(url)
    networks = set()
    cidrs = data.get("result", {}).get("ipv4_cidrs", [])
    for cidr in cidrs:
        net = parse_ipv4_network(cidr)
        if net:
            networks.add(net)
    print(f"[INFO] Found {len(networks)} Cloudflare IPv4 subnets.")
    return networks

def get_cloudfront_ips():
    print("[INFO] Fetching AWS CloudFront IP ranges...")
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    data = fetch_json(url)
    networks = set()
    for item in data.get("prefixes", []):
        if item.get("service") == "CLOUDFRONT":
            net = parse_ipv4_network(item.get("ip_prefix"))
            if net:
                networks.add(net)
    print(f"[INFO] Found {len(networks)} AWS CloudFront IPv4 subnets.")
    return networks

def get_fastly_ips():
    print("[INFO] Fetching Fastly IP ranges...")
    url = "https://api.fastly.com/public-ip-list"
    data = fetch_json(url)
    networks = set()
    for cidr in data.get("addresses", []):
        net = parse_ipv4_network(cidr)
        if net:
            networks.add(net)
    print(f"[INFO] Found {len(networks)} Fastly IPv4 subnets.")
    return networks

def get_google_ips():
    print("[INFO] Fetching Google & Google Cloud IP ranges...")
    networks = set()
    
    # Google Services
    try:
        goog_data = fetch_json("https://www.gstatic.com/ipranges/goog.json")
        for item in goog_data.get("prefixes", []):
            net = parse_ipv4_network(item.get("ipv4Prefix"))
            if net:
                networks.add(net)
    except Exception as e:
        print(f"[ERROR] Failed to fetch Google IP ranges: {e}", file=sys.stderr)
        
    # Google Cloud
    try:
        cloud_data = fetch_json("https://www.gstatic.com/ipranges/cloud.json")
        for item in cloud_data.get("prefixes", []):
            net = parse_ipv4_network(item.get("ipv4Prefix"))
            if net:
                networks.add(net)
    except Exception as e:
        print(f"[ERROR] Failed to fetch Google Cloud IP ranges: {e}", file=sys.stderr)

    print(f"[INFO] Found {len(networks)} Google & Google Cloud IPv4 subnets.")
    return networks

def get_akamai_ips():
    print("[INFO] Fetching Akamai BGP IP ranges...")
    # Key Akamai ASNs: AS20940 (Akamai Technologies), AS16625 (Akamai International), AS35994 (Akamai Edge)
    asns = ["AS20940", "AS16625", "AS35994"]
    networks = set()
    for asn in asns:
        url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"
        try:
            data = fetch_json(url)
            asn_prefixes = 0
            for item in data.get("data", {}).get("prefixes", []):
                net = parse_ipv4_network(item.get("prefix"))
                if net:
                    networks.add(net)
                    asn_prefixes += 1
            print(f"[INFO] Akamai {asn}: {asn_prefixes} prefixes fetched.")
        except Exception as e:
            print(f"[ERROR] Failed to fetch Akamai {asn}: {e}", file=sys.stderr)

    print(f"[INFO] Found total {len(networks)} Akamai IPv4 subnets.")
    return networks

def generate_rsc_content(list_name, comment, collapsed_networks):
    lines = ["/ip firewall address-list"]
    for net in collapsed_networks:
        lines.append(f'add list={list_name} address={net} comment="{comment}"')
    return "\n".join(lines) + "\n"

def main():
    parser = argparse.ArgumentParser(description="Generate RouterOS IP Lists")
    parser.add_argument("--target", choices=["all", "github", "global-forwork"], default="all",
                        help="Target list to generate (default: all)")
    args = parser.parse_args()

    gh_networks = None
    if args.target in ("all", "github"):
        gh_networks = get_github_ips()
        collapsed_gh = list(ipaddress.collapse_addresses(gh_networks))
        rsc_gh = generate_rsc_content("GitHub", "GITHUB_IP_LIST", collapsed_gh)
        with open("IMPORT_GITHUB_IPLIST.rsc", "w", encoding="utf-8") as f:
            f.write(rsc_gh)
        print(f"[SUCCESS] Wrote {len(collapsed_gh)} collapsed CIDRs to IMPORT_GITHUB_IPLIST.rsc")

    if args.target in ("all", "global-forwork"):
        if gh_networks is None:
            gh_networks = get_github_ips()
        cf_networks = get_cloudflare_ips()
        aws_networks = get_cloudfront_ips()
        fastly_networks = get_fastly_ips()
        google_networks = get_google_ips()
        akamai_networks = get_akamai_ips()

        all_forwork = (
            gh_networks
            | cf_networks
            | aws_networks
            | fastly_networks
            | google_networks
            | akamai_networks
        )
        print(f"[INFO] Total raw subnets collected for Global-ForWork: {len(all_forwork)}")
        collapsed_forwork = list(ipaddress.collapse_addresses(all_forwork))
        rsc_forwork = generate_rsc_content("Global-ForWork", "GLOBAL_FORWORK_IP_LIST", collapsed_forwork)
        with open("IMPORT_GLOBAL_FORWORK_IPLIST.rsc", "w", encoding="utf-8") as f:
            f.write(rsc_forwork)
        print(f"[SUCCESS] Wrote {len(collapsed_forwork)} collapsed CIDRs to IMPORT_GLOBAL_FORWORK_IPLIST.rsc")

if __name__ == "__main__":
    main()
