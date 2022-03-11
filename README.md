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
- set the DISPLAY environment variable to an unreachable alias
```export DISPLAY=nodisplay```

## A quick tour

- We will use the loopback.j0 template to add a loopback to the cisco router reachable by ssh at the address 10.0.0.1 with the cisco/cisco credentials
- Check router's credentials and open a terminal with `setsid -w ssh -l cisco 10.0.0.1'`. Use following configuration and command to monitor the changes :
```
conf t
ip scp server enable
aaa accounting commands local
end
ter mon
```
- In a new terminal window, check template content :
```
cat loopback.j0
interface Loopback $loop_nb
  ip address $ip_addr 255.255.255.255
end
```
- Generate the configuration for loopback #777 and ip address 7.7.7.7/32 and send it to the router :
```
python CiscoCfg.py -a 10.0.0.1 -u cisco -t loopback.j0 -d '{ "loop_nb": 777, "ip_addr": "7.7.7.7" }'
```


## Advanced features :
- use a json file for the -d parameter instead of inline input by adding a @ to the file reference (same as curl)
- use the tipyte jinja2-like template engine (congratulations to Eric Pruitt) with `-E tipyte`
- dryrun mode with -D [-o /dev/stdout]
- delayed configuration change with -w parameter and EEM

