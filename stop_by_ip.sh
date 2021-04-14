IP="192.168.1.$1"
echo $IP

# get id and status
ID=`aliyun ecs DescribeInstances --PrivateIpAddresses "[\"$IP\"]" | jq -r '.Instances.Instance[0].InstanceId'`
STATUS=`aliyun ecs DescribeInstances --PrivateIpAddresses "[\"$IP\"]" | jq -r '.Instances.Instance[0].Status'`

echo $ID $STATUS

if [[ $STATUS != 'Running' ]]; then
    echo 'Not Running!'
    exit
fi

ssh $IP

# TODO: now can stop the machine. but it is easier to shutdown in slave, and delete all stopped machines.
aliyun ecs StopInstances --InstanceId.1 i-hp3cszjdrc53ljft6otu

