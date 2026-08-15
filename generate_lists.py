#!/usr/bin/env python3
"""
RouterOS Address List Generator for:
- CN (China IP + Bilibili + WeChat/Tencent + Internal)
- GitHub
- Global-ForWork (Cloudflare, Akamai, CloudFront, Fastly, Google, Google Cloud CDN, OpenAI, Anthropic, Grok, Discord, Medium, Perplexity, GitHub)
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

def fetch_text(url, retries=3, delay=2):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8")
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

def get_asn_prefixes(asn):
    networks = set()
    url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"
    try:
        data = fetch_json(url)
        for item in data.get("data", {}).get("prefixes", []):
            net = parse_ipv4_network(item.get("prefix"))
            if net:
                networks.add(net)
    except Exception as e:
        print(f"[ERROR] Failed to fetch BGP prefixes for {asn}: {e}", file=sys.stderr)
    return networks

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
    asns = ["AS20940", "AS16625", "AS35994"]
    networks = set()
    for asn in asns:
        nets = get_asn_prefixes(asn)
        print(f"[INFO] Akamai {asn}: {len(nets)} prefixes fetched.")
        networks |= nets

    print(f"[INFO] Found total {len(networks)} Akamai IPv4 subnets.")
    return networks

def get_openai_ips():
    print("[INFO] Fetching OpenAI IP ranges...")
    urls = [
        "https://openai.com/chatgpt-actions.json",
        "https://openai.com/gptbot.json",
        "https://openai.com/chatgpt-user.json",
        "https://openai.com/searchbot.json"
    ]
    networks = set()
    for u in urls:
        try:
            data = fetch_json(u)
            for item in data.get("prefixes", []):
                net = parse_ipv4_network(item.get("ipv4Prefix"))
                if net:
                    networks.add(net)
        except Exception as e:
            print(f"[WARN] Failed fetching OpenAI feed {u}: {e}", file=sys.stderr)
            
    asn_nets = get_asn_prefixes("AS400585")
    networks |= asn_nets
    print(f"[INFO] Found {len(networks)} OpenAI IPv4 subnets.")
    return networks

def get_anthropic_ips():
    print("[INFO] Fetching Anthropic IP ranges...")
    networks = get_asn_prefixes("AS399358")
    print(f"[INFO] Found {len(networks)} Anthropic IPv4 subnets.")
    return networks

def get_grok_ips():
    print("[INFO] Fetching Grok / X IP ranges...")
    networks = get_asn_prefixes("AS13414")
    print(f"[INFO] Found {len(networks)} Grok / X IPv4 subnets.")
    return networks

def get_discord_ips():
    print("[INFO] Fetching Discord IP ranges...")
    networks = get_asn_prefixes("AS12414")
    print(f"[INFO] Found {len(networks)} Discord IPv4 subnets.")
    return networks

def get_perplexity_ips():
    print("[INFO] Fetching Perplexity IP ranges...")
    urls = [
        "https://www.perplexity.com/perplexitybot.json",
        "https://www.perplexity.com/perplexity-user.json"
    ]
    networks = set()
    for u in urls:
        try:
            data = fetch_json(u)
            for item in data.get("prefixes", []):
                net = parse_ipv4_network(item.get("ipv4Prefix"))
                if net:
                    networks.add(net)
        except Exception as e:
            print(f"[WARN] Failed fetching Perplexity feed {u}: {e}", file=sys.stderr)
    print(f"[INFO] Found {len(networks)} Perplexity IPv4 subnets.")
    return networks

def get_cn_ips():
    print("[INFO] Fetching China IP lists...")
    urls = [
        "https://raw.githubusercontent.com/mayaxcn/china-ip-list/master/chnroute.txt",
        "https://raw.githubusercontent.com/misakaio/chnroutes2/master/chnroutes.txt"
    ]
    networks = set()
    for u in urls:
        try:
            text = fetch_text(u)
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    net = parse_ipv4_network(line)
                    if net:
                        networks.add(net)
        except Exception as e:
            print(f"[ERROR] Failed fetching {u}: {e}", file=sys.stderr)

    print("[INFO] Fetching Bilibili and WeChat/Tencent IP ranges...")
    bilibili_asns = ["AS59077", "AS140633"]
    wechat_asns = ["AS132203", "AS45090", "AS133475"]
    for asn in bilibili_asns:
        nets = get_asn_prefixes(asn)
        print(f"[INFO] Bilibili {asn}: {len(nets)} prefixes fetched.")
        networks |= nets
    for asn in wechat_asns:
        nets = get_asn_prefixes(asn)
        print(f"[INFO] WeChat/Tencent {asn}: {len(nets)} prefixes fetched.")
        networks |= nets

    print(f"[INFO] Total raw subnets collected for CN (with Bilibili & WeChat): {len(networks)}")
    return networks

def generate_rsc_content(list_name, comment, collapsed_networks, extra_lines=None):
    lines = ["/ip firewall address-list"]
    for net in collapsed_networks:
        lines.append(f'add list={list_name} address={net} comment="{comment}"')
    if extra_lines:
        lines.extend(extra_lines)
    return "\n".join(lines) + "\n"

def main():
    parser = argparse.ArgumentParser(description="Generate RouterOS IP Lists")
    parser.add_argument("--target", choices=["all", "cn", "github", "global-forwork"], default="all",
                        help="Target list to generate (default: all)")
    args = parser.parse_args()

    if args.target in ("all", "cn"):
        cn_networks = get_cn_ips()
        collapsed_cn = list(ipaddress.collapse_addresses(cn_networks))
        
        # IMPORT_CN_IPLIST.rsc
        rsc_cn = generate_rsc_content("CN", "CHINA_IP_LIST", collapsed_cn)
        with open("IMPORT_CN_IPLIST.rsc", "w", encoding="utf-8") as f:
            f.write(rsc_cn)
        print(f"[SUCCESS] Wrote {len(collapsed_cn)} collapsed CIDRs to IMPORT_CN_IPLIST.rsc")

        # IMPORT_CN_IPLIST_INTERNAL.rsc
        internal_lines = [
            'add list=CN_WITH_IIP address=10.0.0.0/8 comment="CHINA_IP_LIST_INTERNAL"',
            'add list=CN_WITH_IIP address=172.16.0.0/12 comment="CHINA_IP_LIST_INTERNAL"',
            'add list=CN_WITH_IIP address=192.168.0.0/16 comment="CHINA_IP_LIST_INTERNAL"'
        ]
        rsc_cn_internal = generate_rsc_content("CN_WITH_IIP", "CHINA_IP_LIST_INTERNAL", collapsed_cn, internal_lines)
        with open("IMPORT_CN_IPLIST_INTERNAL.rsc", "w", encoding="utf-8") as f:
            f.write(rsc_cn_internal)
        print(f"[SUCCESS] Wrote {len(collapsed_cn) + 3} rules to IMPORT_CN_IPLIST_INTERNAL.rsc")

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
        openai_networks = get_openai_ips()
        anthropic_networks = get_anthropic_ips()
        grok_networks = get_grok_ips()
        discord_networks = get_discord_ips()
        perplexity_networks = get_perplexity_ips()

        all_forwork = (
            gh_networks
            | cf_networks
            | aws_networks
            | fastly_networks
            | google_networks
            | akamai_networks
            | openai_networks
            | anthropic_networks
            | grok_networks
            | discord_networks
            | perplexity_networks
        )
        print(f"[INFO] Total raw subnets collected for Global-ForWork: {len(all_forwork)}")
        collapsed_forwork = list(ipaddress.collapse_addresses(all_forwork))
        rsc_forwork = generate_rsc_content("Global-ForWork", "GLOBAL_FORWORK_IP_LIST", collapsed_forwork)
        with open("IMPORT_GLOBAL_FORWORK_IPLIST.rsc", "w", encoding="utf-8") as f:
            f.write(rsc_forwork)
        print(f"[SUCCESS] Wrote {len(collapsed_forwork)} collapsed CIDRs to IMPORT_GLOBAL_FORWORK_IPLIST.rsc")

if __name__ == "__main__":
    main()
