import sys, yaml

try:
    import json
except ImportError:
    import simplejson as json

datain = yaml.load(open(sys.argv[1], 'r').read())

dataout = json.dumps(datain)

open(sys.argv[2], 'w').write(dataout)