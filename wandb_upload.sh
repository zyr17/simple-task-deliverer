THREADS=4
WAIT_TIME=10m

if [[ $# -eq 0 ]]; then
    TARGETF=`pwd`
else
    TARGETF="$@"
fi

if [[ ! $TARGETF == */wandb ]]; then
    TARGETF="$TARGETF/wandb"
fi

OTFNAME=_upload_one_thread.`uuidgen`.sh

cd $TARGETF

cat << 'EOF' > $OTFNAME
while :; do
    if [[ -z `ls offline* 2>/dev/null` ]]; then
        echo "thread $1 done"
        break
    fi
    for i in `ls | grep offline | shuf`; do
        if [[ -d $i ]]; then
            wandb sync $i && cp -r $i ok && rm -r $i
        fi
    done
    sleep 10s;
done
EOF

chmod +x $OTFNAME

handle_interrupt(){
    rm $OTFNAME
    exit 1
}

trap 'handle_interrupt' INT

if [[ ! -e ok ]]; then
    mkdir ok
fi

# if [[ $# -ge 1 ]]; then
#     THREADS=$1
# fi

i=1
while [[ $i -le $THREADS ]]; do
    echo $i
    bash -c "WANDBUPLOAD= ; echo $PWD; cd $PWD; ./$OTFNAME $i" &
    i=`expr $i + 1`
done

while :; do
    sleep $WAIT_TIME;
    # if [[ -n `ps aux | grep '[W]ANDBUPLOAD'` ]]; then
    if [[ -n `ls offline* 2>/dev/null` ]]; then
        echo kill all sync process to avoid stuck
        kill `ps aux | grep "[w]andb sync" | awk '{print $2}'`
    else
        echo all jobs clean, killall and exit
        kill `ps aux | grep "[w]andb sync" | awk '{print $2}'` 2>/dev/null
        break
    fi
done

rm $OTFNAME
