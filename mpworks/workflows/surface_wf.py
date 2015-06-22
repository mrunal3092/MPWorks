import os
from pymongo import MongoClient
from fireworks.core.firework import FireWork, Workflow
from fireworks import ScriptTask
from fireworks.core.launchpad import LaunchPad
from pymatgen.core.metal_slab import MPSlabVaspInputSet
from mpworks.firetasks.surface_tasks import RunCustodianTask, VaspDBInsertTask, WriteSurfVaspInput
from custodian.vasp.jobs import VaspJob


import os
from pymongo import MongoClient
from fireworks.core.firework import FireWork, Workflow
from fireworks.core.launchpad import LaunchPad


def create_surface_workflows(miller_index, api_key, element, k_product=50):

    fws = []
    fw = FireWork([WriteSurfVaspInput(element=element,
                                      miller_index=miller_index,
                                      api_key=api_key)])
    fws.append(fw)
    wf = Workflow(fws, name="3D Metal Surface Energy Workflow")
    
    return wf


launchpad = LaunchPad.from_file(os.path.join(os.environ["HOME"],
                                              "surf_wf_tests", "my_launchpad.yaml"))
launchpad.reset('', require_password=False)

wf = create_surface_workflows((0,0,1), " mlcC4gtXFVqN9WLv", "Mo")
launchpad.add_wf(wf)
