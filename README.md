# cisco_ssh_cfg

A script written for micro python which remotely configures a cisco router using templating.
Templating is based either on the python string template or on the tiny [tipyte engine](https://github.com/ericpruitt/tipyte) from Eric Pruitt.

## Installation

- copy the python files tipyte.py and cisco_ssh_cfg.py into a directory
- create an executable file `askpassh.sh` which contains
```
echo '<your ssh password>'
```
- define the `SSK_ASKPASS` environment variable to the file and make it point to the previous file
```
export SSH_ASKPASS=/home/user/cisco_ssh_cfg/askpass.sh
```

## A quick tour

- create the simple template using the commands 
```
cat << EOF > 'loop.j0'
interface Loopback $loop_nb
  ip address $ip_add 255.255.255.255
end
```
- send the configuration for loopback 777 and ip address 7.7.7.7/32 to the router already configured with the managment address 10.0.0.1 :
```
python cisco_ssh_cfg.py -a 10.0.0.1 -t loop.j0 -d '{ "loop_nb": 777, "ip_add": "7.7.7.7" }'
```


