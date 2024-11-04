#!/bin/sh
mkdir -p ./pbr
cd ./pbr

# AS4809 BGP
wget --no-check-certificate -c -O tg.txt https://core.telegram.org/resources/cidr.txt

{
echo "/ip firewall address-list"

for net in $(grep -v '^#' tg.txt) ; do
  echo "add list=TG-IP address=$net comment=Telegram_IP_LIST"
done

} > ../IMPORT_TG_IPLIST.rsc

cd ..
rm -rf ./pbr
