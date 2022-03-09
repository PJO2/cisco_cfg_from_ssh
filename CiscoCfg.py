# -----------------------------------------------------------------------------
# resolve a template and send the configuration to a router 
# Note : 
#    SSH_ASKPASS must point to an executable file which contains echo 'NUAR pwd'
# by PJO
# ----------------------------------------------------------------------------

import optparse
import json
import string
import os
import tempfile
import subprocess

def read_command_line ():
    """ handle command line """
    parser = optparse.OptionParser()
    # configure option parsing with default destination (longnames)
    parser.add_option('-t', '--template', help='The template to be applied')
    parser.add_option('-o', '--output',   help='The output file (optional)',                           
                                          default=tempfile.NamedTemporaryFile().name)
    parser.add_option('-a', '--address',  help='DNS name or current ip admin address')
    parser.add_option('-u', '--user',     help='user to be used for scp',          default='')
    parser.add_option('-d', '--data',     help="The template's variables in a json object (optional)", 
                                          default = '{}')
    parser.add_option('-w', '--wait',     help="wait n seconds before applying template (optional)",   
                                          type="int", default=0)
    parser.add_option('-E', '--engine',   help="Template engine [string, tipyte]", default='string')
    parser.add_option('-D', '--dryrun',   action="store_true", default=False,
                                          help="Only resolve the template, do not send to host")
    # Parse the argument
    args,_ = parser.parse_args()
    data = json.loads(args.data)
    return args, data

def render_template(engine, tmpl_name, out_file, data):
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
       raise AttrbuteError("Unknown template engine")
   # write result in a file
   with open (out_file, 'w') as w:
       w.write(result)

def scp_file(filename, user, dest):
    """ download the config file to the device """
    os_tmpl_cmd = "setsid scp {file} {user}{at}{dest}:bootflash:/{basename}"
    os_cmd = os_tmpl_cmd.format(file=filename, 
                                user=user, dest=dest, at ='@' if user!='' else '', 
                                basename=os.path.basename(filename))
    print ("starting upload with cmd: " + os_cmd)
    rc = os.system (os_cmd)
    return rc==0


def load_file_delayed(filename, user, dest, wait):
    """ activate the configuration file via EEM """
    eem_tmpl = """
event manager applet RUN authorization bypass
 event timer countdown time {wait} maxrun 60
 action 0.1 cli command "enable"
 action 1.0 cli command "copy bootflash:/{file} running-config" pattern "running-config"
 action 1.1 cli command "running-config"
 action 2.0 syslog msg "Configuration done by Merge.py"
end
"""
    with tempfile.NamedTemporaryFile() as temp:
         eem_cfg = eem_tmpl.format(wait=wait, file=os.path.basename(filename))
         temp.write(eem_cfg)
         temp.flush()
         rc = os.system ("setsid scp {name} {user}{at}{dest}:running-config".format(name=temp.name, 
                                                user=user, dest=dest, at ='@' if user!='' else ''))



def load_file_immediate(filename, user, dest):
    """ activate the configuration file : basically send a copy file running-config"""
    os_cmd = [ 'setsid', 
                   'ssh',
                   "{user}{at}{dest}".format(user=user, dest=dest, at='@' if user!='' else ''),
                   "copy bootflash:/{file} running-config".format(file=os.path.basename(filename))
                  ]
    print ("command is ", os_cmd)
    # now we do it with subprocess and send a EOL to validate the copy
    p = subprocess.Popen(os_cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.stdin.write("\n")   # <-- magic happens here
    out, err = p.communicate ()
    print (out)
    return err==0 
 

if __name__ == "__main__":
    args,data = read_command_line()                     # parse command line
    render_template (args.engine, args.template, args.output, data)  # resolve template
    if args.dryrun:
       print("template resolved in file {file}\n".format(file=args.output))
    else:
        rc = scp_file (args.output, args.user, args.dest)   # send resolved template to device
        # ----     load the config file into running-config ----
        if args.wait==0:
            load_file_immediate(args.output, args.user, args.dest)  # activate file
        else:
            load_file_delayed(args.output, args.user, args.dest, args.wait)
        os.remove(args.output)

