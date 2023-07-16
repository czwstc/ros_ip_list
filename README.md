## 由Github Action自动构建的RouterOS Address List
![Status](https://github.com/czwstc/ros_ip_list/actions/workflows/main.yml/badge.svg)

### 已添加的IP Range：
CN IP：
ip段信息取自 [china-ip-list](https://github.com/mayaxcn/china-ip-list)

Google IP:
ip段信息取自 [Google-ip-list](https://support.google.com/a/answer/10026322?hl=en)


### 策略路由分流的实现方法：
/System/Scripts 中创建脚本

CN IP：
**IMPORT_CN_IPLIST.rsc** 是往Firewall - address lists 里生ip段列表。
```
/file remove [find name="IMPORT_CN_IPLIST.rsc"]
/tool fetch url="https://ghproxy.com/https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_CN_IPLIST.rsc"
:if ([:len [/file find name=IMPORT_CN_IPLIST.rsc]] > 0) do={
/ip firewall address-list remove [find comment="CHINA_IP_LIST"]
/import IMPORT_CN_IPLIST.rsc
}
```

Google IP:
**IMPORT_GOOGLE_IPLIST.rsc** 是往Firewall - address lists 里生ip段列表。
```
/file remove [find name="IMPORT_GOOGLE_IPLIST.rsc"]
/tool fetch url="https://ghproxy.com/https://raw.githubusercontent.com/czwstc/ros_ip_list/main/IMPORT_GOOGLE_IPLIST.rsc"
:if ([:len [/file find name=IMPORT_CN_IPLIST.rsc]] > 0) do={
/ip firewall address-list remove [find comment="GOOGLE_IP_LIST"]
/import IMPORT_GOOGLE_IPLIST.rsc
}
```

用于Firewall - mangle页，通过dst-addrss= 引用
