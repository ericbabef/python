#-*- coding: utf-8 -*-
from traitements_dt_dict import TraitementsDtDict
import json

class ExecutionDtDict(TraitementsDtDict):
    """
        Execution DT DICT
    """

# ----------------------------------------------------------------------
if __name__ == "__main__":

    with open("config.json", 'r') as f:
        conf = json.load(f)

    dt_dict = ExecutionDtDict(conf)
    execution_script = dt_dict.intersect_geom()
    for item in execution_script:
        print("ok")