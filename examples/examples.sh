# set environment variables SSH_ASKPASS and DISPLAY
# check that askpass return correctly your password
export SSH_ASKPASS=$(pwd)/askpass.sh
export DISPLAY=nodisplay

DEVICE=172.16.63.232

# use the string template to create Loopback 777 on device 10.0.0.1
python ../CiscoCfg.py -a $DEVICE -u cisco -t loopback.j0 -d '{ "loop_nb": 777, "ip_addr": "7.7.7.7" }' 

# use the more advanced tipyte template to create Loopback 777 to 779 on device 10.0.0.1 
#   using data from loopbacks.json and delayed by 60 seconds
python ../CiscoCfg.py -a $DEVICE -u cisco -t loopbacks.j2 -d @loopbacks.json -E tipyte -w 60

