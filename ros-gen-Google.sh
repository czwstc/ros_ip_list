#!/bin/sh
mkdir -p ./pbr
cd ./pbr

# GoogleIP
wget --no-check-certificate -c -O goog.json https://www.gstatic.com/ipranges/goog.json
jq -r '.prefixes[] | select(has("ipv4Prefix")) | .ipv4Prefix' goog.json | cut -d '"' -f 1 > google.txt
{
echo "/ip firewall address-list"

for net in $(cat google.txt) ; do
  echo "add list=Google address=$net comment=GOOGLE_IP_LIST"
done

} > ../IMPORT_GOOGLE_IPLIST.rsc

cd ..
rm -rf ./pbr
