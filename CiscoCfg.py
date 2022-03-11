# -----------------------------------------------------------------------------
# resolve a template and send the configuration to a cisco device 
# by PJO - March 2022                    https://github.com/PJO2/cisco_ssh_cfg
#
# Note : Two environment variables must be set before executing cisco_ssh_cfg
#    SSH_ASKPASS must point to an executable file which contains echo 'SSH pwd'
#    DISPLAY     must specify an inaccessible terminal (ex 'nodisplay')
# ----------------------------------------------------------------------------

import optparse
import json
import string
import os
import tempfile
import subprocess

# disable prompt for new ssh connections (setsid may not behave correctly)
SSH_OPTIONS = '-o StrictHostKeyChecking=no'
SETSID_OPTIONS = '-w'

# Cisco location to store file before putting it in runing-config
CISCO_FILESYSTEM  =   "bootflash:/"
RUNNING_CONFIG    =   "running-config"
EEM_TEMPLATE      =   """
event manager applet CiscoCfgRUN authorization bypass
  event timer countdown time {wait} maxrun 60
  action 0.1 cli command "enable"
  action 1.0 cli command "copy bootflash:/{file} running-config" pattern "running-config"
  action 1.1 cli command "running-config"
  action 2.0 syslog msg "Configuration upload done by CiscoCfg.py"
  action 3.0 cli command "configure terminal"
  action 3.1 cli command "no event manager applet CiscoCfgRUN"
  action 3.2 cli command "end"
end
"""


def render_template(tmpl_name, out_file, data, engine):
   """ read the 'template' and resolve it with safe_substitute """
   if engine=="string":
       with open(tmpl_name, 'r') as f:
           src = string.Template(f.read())
           result = src.safe_substitute(data)
   elif engine=="tipyte":
       import tipyte
       def nothing(a):
          return a
       render_inbox = tipyte.template_to_function(tmpl_name, escaper=nothing)
       result = render_inbox(data)  # do not use kwargs syntax data=data
   else:
       raise AttributeError("Unknown template engine")
   # write result in a file
   with open (out_file, 'w') as w:
       w.write(result)


def scp_file(filename, username, dest, path):
    """ download the config file to the device """
    os_scp_tmpl_cmd = ( [
                        'setsid', ]		# <-- first magic to skip ssh from asking password
                      + SETSID_OPTIONS.split() + [
                        'scp', ] 
                      + SSH_OPTIONS.split() + [
                        '{file}',
                        '{username}{at}{dest}:{path}',
                        ] )
    os_cmd = []
    for word in os_scp_tmpl_cmd:
       os_cmd.append ( word.format( file=filename, 
                                    username=username, 
                                    dest=dest, 
                                    at ='@' if username!='' else '', 
                                    path=path )
                     )
    print ("starting upload with cmd: ", os_cmd)
    p = subprocess.Popen(os_cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.stdin.write(b"\n")   # <-- second magic happens here for sending copy confirmation to the device 
    out, err = p.communicate()
    if p.returncode!=0:
       print ("Error: subprocess return:\n{err}".format(err=err))
       raise OSError("Error during file transfer")
    print (out)
    return err 


def load_file_delayed(filename, dest, username, wait):
    """ activate the configuration file via EEM """
    with tempfile.NamedTemporaryFile() as temp:
         eem_cfg = EEM_TEMPLATE.format(wait=wait, file=os.path.basename(filename))
         temp.write(eem_cfg)
         temp.flush()
         rc = scp_file(temp.name, username, dest, RUNNING_CONFIG)
         return rc


# The global API
def ssh_cfg (dest, tmpl_name, out_file, data=None, engine='string', username='', delay=0, dryrun=False):
    """ render a template and send it to a remote cisco device 

    Keywords arguments:
       dest:      the Cisco device where to push the configuration
       tmpl_name: the filename of the configuration template
       out_file:  the name of the file used to render the template, mais be /dev/stdout for dryrun
       data:      a dictinnary which contains the data
       engine:    the template engine used, default is standard string Template, 
                  may be pitype for Jinja2 like templating
       username:  the user used to log the device
       delay:     differ the execution of the configuration by delay seconds
       dryrun:    test mode, do no send the configuration to the device
    """
    render_template (tmpl_name, out_file, data, engine)  # resolve template
    if dryrun:
        print ("template resolved into {out_file}".format(out_file=out_file))
    else:
        if delay==0:
            rc = scp_file (out_file, username, dest, RUNNING_CONFIG)
        else:
            # send resolved template to device as a file, then use EEM to load it into running-config after countdown
            rc = scp_file (out_file, username, dest, CISCO_FILESYSTEM+os.path.basename(out_file))
            load_file_delayed(out_file, dest, username, delay)
        os.remove(out_file)


if __name__ == "__main__":
    def read_command_line ():
        """ handle command line """
        parser = optparse.OptionParser()
        # configure option parsing with default destination (longnames)
        parser.add_option('-a', '--address',  help='DNS hostname or current ip admin address')
        parser.add_option('-u', '--username', help='username to be used for configuring device', default='')
        parser.add_option('-t', '--template', help='The template to be applied')
        parser.add_option('-d', '--data',     help="The template's variables in a json object (optional)", 
                                              default = '{}')
        parser.add_option('-o', '--output',   help='The output file (optional)',                           
                                              default=tempfile.NamedTemporaryFile().name)
        parser.add_option('-w', '--wait',     help="wait n seconds before applying template (optional)",   
                                              type="int", default=0)
        parser.add_option('-E', '--engine',   help="Template engine [string, tipyte]", default='string')
        parser.add_option('-D', '--dryrun',   action="store_true", default=False,
                                              help="Only resolve the template, do not send to host")
        # Parse the argument
        args,_ = parser.parse_args()
        return args


    args = read_command_line()                     # parse command line
    # deserialize data 
    if args.data.startswith('@'): # if args.data starts with '@' it points to a file otherwise it is the data
        with open(args.data[1:], 'r') as f:
              data = json.load(f)
    else:
              data = json.loads(args.data)
    # Call main API
    ssh_cfg (dest      = args.address, 
             tmpl_name = args.template,
             out_file  = args.output,
             data      = data,
             engine    = args.engine,
             username  = args.username, 
             delay     = args.wait,
             dryrun    = args.dryrun)



