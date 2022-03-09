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
import subprocess

# -----      Read the command line arguments --
parser = optparse.OptionParser()
# configure option parsing with default destination (longnames)
parser.add_option('-t', '--template', help='The template to be applied')                    
parser.add_option('-o', '--output',   help='The output file')
parser.add_option('-n', '--dest',     help='DNS name or current ip admin address')
parser.add_option('-u', '--user',     help='user to be used for scp', default='')
parser.add_option('-d', '--data',     help="The template's variables in a json object")

# Parse the argument
args,_ = parser.parse_args()
data = json.loads(args.data)

print data

# -----     Template processing ---
# read the 'template' and resolve it with safe_substitute
with open(args.template, 'r') as f:
    src = string.Template(f.read())
    result = src.safe_substitute(data)

# -----     Send to device line by line --
print ("starting batch with cmds: " + result)
# write result in a file
with open (args.output, 'w') as w:
   for line in [ l for l in result.split("\n") if l!='' ]:
      os_cmd = ['setsid', 'ssh', 
                "{user}{at}{dest}".format(user=args.user, dest=args.dest, at='@' if args.user!='' else ''),
                "'" + line + "'" ]
      print ("command is ", os_cmd)
      p = subprocess.Popen(os_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out,err = p.communicate ()
      print (out)
      w.write(out) 

print ("done, return code {err}".format(err=err))

