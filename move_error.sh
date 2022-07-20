#!/bin/bash

# check one exp folder, filter error logs and move them into error folder;
# then select error wandb file to avoid uploading crashed logs.

if [[ -z $1 ]]; then
    echo one argument means operation folder
    exit 1
fi

cd $1

mkdir -p errors/wandb

for i in *log; do if [[ -n `tail -n 1 $i | grep -P "unsorted double linked list corrupted|invalid pointer"` ]]; then IP=`echo $i | sed 's/.*\(192\.168\.[0-9]\+\.[0-9]\+\).*/\1/'`; echo $IP; tail -n 1 $i; ssh $IP shutdown now; fi; done

# ssh to shutdown all running slaves, as they are stuck. if not want to stop
# running slaves, comment this.
# for i in *log; do if [[ -n `tail -n 1 $i | grep -P "\[INFO \] epoch"` ]]; then IP=`echo $i | sed 's/.*\(192\.168\.[0-9]\+\.[0-9]\+\).*/\1/'`; echo $IP; tail -n 1 $i; ssh $IP shutdown now; fi; done; exit

# check all log. if it contains `fail too many times` or last line is `invalid
# pointer` or `closed by remote host`, then this run is failed/crash on
# running/shutdown by previous script. find its wandb id, and move the 
# corresponsing log and wandb into errors folder.
COUNTER=0
for i in *log; do 
    if [[ -n `cat "$i" | grep "fail too many times"` || -n `tail -n 1 "$i" | grep -P "unsorted double linked list corrupted|invalid pointer|closed by remote host"` ]]; then
        wandb=`cat $i | grep "wandb id:" | awk '{print $5}' | tr '\r' ' '`; 
        if [[ -z $wandb ]]; then 
            wandb=`tail -n 10 $i | grep "wandb sync" | awk '{print $4}' | sed 's/.*_[0-9]*-//'`; 
        fi; 
        if [[ -n $wandb ]]; then 
            mv /app/AAAI2023/wandb/*${wandb} errors/wandb/; 
            mv $i errors/; 
            COUNTER=`expr $COUNTER + 1`
        else 
            echo $i no wandb; 
        fi; 
    fi; 
done
echo moved $COUNTER wandb files
