#!/bin/bash

# use aliyun cli to find all stopped ecs in default region, and remove them.

# get
RESPONSE=`aliyun ecs DescribeInstances --PageSize 1`
ALLSERVERNUMBER=`echo $RESPONSE | jq -r '.TotalCount'`
echo "Found instance number: $ALLSERVERNUMBER," | tr '\n' ' '

RESPONSE=`aliyun ecs DescribeInstances --PageSize 1 --Status Stopped`
ALLSERVERNUMBER=`echo $RESPONSE | jq -r '.TotalCount'`
echo Found stopped number: $ALLSERVERNUMBER

SERVERNUMBER=$ALLSERVERNUMBER

STARTNUMBER=0
PAGENUMBER=1
ONEPAGE=100

while [[ $STARTNUMBER -lt $ALLSERVERNUMBER ]]; do

    RESPONSE=`aliyun ecs DescribeInstances --PageSize $ONEPAGE --PageNumber $PAGENUMBER --Status Stopped | jq ".Instances"`

    for i in {0..99}; do
        if [[ `expr $i + $STARTNUMBER` -ge $ALLSERVERNUMBER ]]; then
            break
        fi
        ID=`echo $RESPONSE | jq -r ".Instance[$i].InstanceId"`
        STATUS=`echo $RESPONSE | jq -r ".Instance[$i].Status"`
        PIP=`echo $RESPONSE | jq -r ".Instance[$i].VpcAttributes.PrivateIpAddress.IpAddress[0]"`

        if [[ $ID == 'null' || $STATUS == 'null' ]]; then
            continue
        fi

        if [[ $ID == i-hp3cjmq8kxto3nv8q92j ]]; then
            continue
        fi

        # echo $ID $STATUS $PIP

        if [[ $STATUS == 'Stopped' ]]; then
            echo Delete instance $ID $STATUS $PIP
            aliyun ecs DeleteInstance --InstanceId $ID
        fi

    done

    PAGENUMBER=`expr $PAGENUMBER + 1`
    STARTNUMBER=`expr $STARTNUMBER + $ONEPAGE`

done
