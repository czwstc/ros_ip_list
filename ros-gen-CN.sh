#!/bin/sh
mkdir -p ./pbr
cd ./pbr

# China IP address list
wget --no-check-certificate -c -O CN1.txt https://raw.githubusercontent.com/mayaxcn/china-ip-list/master/chnroute.txt
wget --no-check-certificate -c -O CN2.txt https://raw.githubusercontent.com/misakaio/chnroutes2/master/chnroutes.txt

# IP address aggregator
# Combine both files and remove duplicates, then save to combined.txt
cat CN1.txt CN2.txt | sort | uniq > CN.txt

{
echo "/ip firewall address-list"

# for net in $(cat CN.txt) ; do
for net in $(grep -v '^#' CN.txt) ; do
  echo "add list=CN address=$net comment=CHINA_IP_LIST"
done

} > ../IMPORT_CN_IPLIST.rsc

{
echo "/ip firewall address-list"

for net in $(grep -v '^#' CN.txt) ; do
  echo "add list=CN_WITH_IIP address=$net comment=CHINA_IP_LIST_INTERNAL"
done
echo "add list=CN_WITH_IIP address=10.0.0.0/8 comment=CHINA_IP_LIST_INTERNAL"
echo "add list=CN_WITH_IIP address=172.16.0.0/12 comment=CHINA_IP_LIST_INTERNAL"
echo "add list=CN_WITH_IIP address=192.168.0.0/16 comment=CHINA_IP_LIST_INTERNAL"

} > ../IMPORT_CN_IPLIST_INTERNAL.rsc

cd ..
rm -rf ./pbr
