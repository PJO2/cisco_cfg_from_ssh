# set environment variables SSH_ASKPASS and DISPLAY
# check that askpass return correctly your password
export SSH_ASKPASS=$(pwd)/admin.sh
export DISPLAY=nodisplay

DEVICE=172.16.63.149

# use the more advanced tipyte template to create Loopback 777 to 779 on device 10.0.0.1 
#   using data from loopbacks.json and delayed by 60 seconds
python ../EkinopsCfg.py -a $DEVICE -u admin -t oalb.j2 -d @loopbacks.json -E tipyte -w 5 -o oa.cfg

