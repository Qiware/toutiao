#!/bin/sh


for (( idx=0; idx<20000; idx+=1 ))
do
    wget "http://dianying.2345.com/zq/$idx.html"
done

exit

cat *.html* | grep -e "<p class=\"pTit\"><span class=\"sTit\">" -e "nofollow" | awk -F"title" '{print $2}' > html

echo "    {" >> json
echo "        \"name_cn\" : \"$film\"," >> json
echo "        \"alias\" : \"\"," >> json
echo "        \"actor\" : \"," >> json

while read data
do
    has=`echo $data | grep "nofollow" | wc -l`
    if [ $has -eq 0 ]; then
        echo "\"," >> json
        echo "        \"starring\" : \"\"," >> json
        echo "        \"starring_play\" : \"\"" >> json
        echo "    }," >> json
        echo "    {" >> json
        film=`echo $data | awk -F"\"" '{print $2}'`
        echo "        \"name_cn\" : \"$film\"," >> json
        echo "        \"alias\" : \"\"," >> json
        echo -e "        \"actor\" : \",\c" >> json
        continue
    else
        actor=`echo $data | awk -F"'" '{print $2}'`
        echo -e "$actor,\c" >> json
    fi
done < ./html

echo -e "\"," >> json
echo "        \"starring\" : \"\"," >> json
echo "        \"starring_play\" : \"\"" >> json
echo "    }" >> json

