import os

#Global Config File
class config:
    debug = False

class dev_config(config):
    debug = True

class prod_config(config):
    debug = False
