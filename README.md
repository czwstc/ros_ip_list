## 由 Github Actions 自动构建的 RouterOS Address List
![Status](https://github.com/czwstc/ros_ip_list/actions/workflows/main.yml/badge.svg)

本项目通过 Github Actions 每天定时从各厂商官方 API / BGP 路由表抓取最新的 IPv4 CIDR 网段，自动聚合优化后生成 RouterOS 的 `.rsc` 地址列表脚本。

---

### 已添加的 IP 列表与数据源：

1. **CN IP**:
   - 数据源：[chnroutes2](https://github.com/misakaio/chnroutes2) / [china-ip-list](https://github.com/mayaxcn/china-ip-list)
   - 生成文件：`IMPORT_CN_IPLIST.rsc`、`IMPORT_CN_IPLIST_INTERNAL.rsc`
   - List 名：`CN` / `CN_WITH_IIP`

2. **Google IP**:
   - 数据源：[Google IP ranges](https://support.google.com/a/answer/10026322?hl=en) (`https://www.gstatic.com/ipranges/goog.json`)
   - 生成文件：`IMPORT_GOOGLE_IPLIST.rsc`
   - List 名：`Google`

3. **Telegram IP**:
   - 数据源：[Telegram CIDR](https://core.telegram.org/resources/cidr.txt)
   - 生成文件：`IMPORT_TG_IPLIST.rsc`
   - List 名：`TG-IP`

4. **GitHub IP**:
   - 数据源：[GitHub Meta API](https://api.github.com/meta)
   - 生成文件：`IMPORT_GITHUB_IPLIST.rsc`
   - List 名：`GitHub`

5. **Global-ForWork IP (CDN, AI & 办公综合列表)**:
   - 包含服务与数据源：
     - **Cloudflare**: [Cloudflare IP API](https://api.cloudflare.com/client/v4/ips)
     - **Akamai**: BGP 宣告路由 (AS20940, AS16625, AS35994)
     - **Amazon CloudFront**: [AWS IP Ranges](https://ip-ranges.amazonaws.com/ip-ranges.json)
     - **Fastly**: [Fastly Public IP API](https://api.fastly.com/public-ip-list)
     - **Google & Google Cloud CDN**: [Google Ranges](https://www.gstatic.com/ipranges/goog.json) / [Google Cloud Ranges](https://www.gstatic.com/ipranges/cloud.json)
     - **GitHub**: [GitHub Meta API](https://api.github.com/meta)
     - **OpenAI (ChatGPT / GPTBot / Egress)**: [OpenAI IP Feeds](https://openai.com/chatgpt-actions.json) 与 AS400585
     - **Anthropic (Claude)**: BGP 宣告路由 AS399358 与 CDN 边缘
     - **Grok / X (Twitter)**: BGP 宣告路由 AS13414
     - **Discord (Voice & RTC Relay)**: BGP 宣告路由 AS12414 与 CDN 边缘
     - **Medium**: Cloudflare 边缘托管
     - **Perplexity**: [PerplexityBot / User Feeds](https://www.perplexity.com/perplexitybot.json)
   - 生成文件：`IMPORT_GLOBAL_FORWORK_IPLIST.rsc`
   - List 名：`Global-ForWork`

---

### RouterOS 策略路由分流配置与自动更新：

在 RouterOS 的 `/system script` 中创建定时更新脚本（可配合 `/system scheduler` 定时执行）：

#### 1. GitHub IP 自动更新脚本：
```routeros
/file remove [find name="IMPORT_GITHUB_IPLIST.rsc"]
/tool fetch url="https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_GITHUB_IPLIST.rsc"
:if ([:len [/file find name=IMPORT_GITHUB_IPLIST.rsc]] > 0) do={
  /ip firewall address-list remove [find comment="GITHUB_IP_LIST"]
  /import IMPORT_GITHUB_IPLIST.rsc
}
```

#### 2. Global-ForWork 综合列表自动更新脚本：
```routeros
/file remove [find name="IMPORT_GLOBAL_FORWORK_IPLIST.rsc"]
/tool fetch url="https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_GLOBAL_FORWORK_IPLIST.rsc"
:if ([:len [/file find name=IMPORT_GLOBAL_FORWORK_IPLIST.rsc]] > 0) do={
  /ip firewall address-list remove [find comment="GLOBAL_FORWORK_IP_LIST"]
  /import IMPORT_GLOBAL_FORWORK_IPLIST.rsc
}
```

#### 3. CN IP：
```routeros
/file remove [find name="IMPORT_CN_IPLIST.rsc"]
/tool fetch url="https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_CN_IPLIST.rsc"
:if ([:len [/file find name=IMPORT_CN_IPLIST.rsc]] > 0) do={
  /ip firewall address-list remove [find comment="CHINA_IP_LIST"]
  /import IMPORT_CN_IPLIST.rsc
}
```

#### 4. CN IP with Internal IP：
```routeros
/file remove [find name="IMPORT_CN_IPLIST_INTERNAL.rsc"]
/tool fetch url="https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_CN_IPLIST_INTERNAL.rsc"
:if ([:len [/file find name=IMPORT_CN_IPLIST_INTERNAL.rsc]] > 0) do={
  /ip firewall address-list remove [find comment="CHINA_IP_LIST_INTERNAL"]
  /import IMPORT_CN_IPLIST_INTERNAL.rsc
}
```

#### 5. Google IP:
```routeros
/file remove [find name="IMPORT_GOOGLE_IPLIST.rsc"]
/tool fetch url="https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_GOOGLE_IPLIST.rsc"
:if ([:len [/file find name=IMPORT_GOOGLE_IPLIST.rsc]] > 0) do={
  /ip firewall address-list remove [find comment="GOOGLE_IP_LIST"]
  /import IMPORT_GOOGLE_IPLIST.rsc
}
```

#### 6. Telegram IP:
```routeros
/file remove [find name="IMPORT_TG_IPLIST.rsc"]
/tool fetch url="https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_TG_IPLIST.rsc"
:if ([:len [/file find name=IMPORT_TG_IPLIST.rsc]] > 0) do={
  /ip firewall address-list remove [find comment="Telegram_IP_LIST"]
  /import IMPORT_TG_IPLIST.rsc
}
```

> [!NOTE]
> 在 RouterOS `IP -> Firewall -> Mangle` 或 `Routing -> Rules` 中，通过 `Dst. Address List` 引用上述列表名（如 `GitHub`、`Global-ForWork`、`CN` 等）即可进行分流与策略路由。
