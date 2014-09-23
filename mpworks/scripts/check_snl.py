"""
A runnable script to check all SNL groups
"""
__author__ = 'Patrick Huck'
__copyright__ = 'Copyright 2014, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Patrick Huck'
__email__ = 'phuck@lbl.gov'
__date__ = 'September 22, 2014'

import sys
from argparse import ArgumentParser
from mpworks.snl_utils.snl_mongo import SNLMongoAdapter
from mpworks.snl_utils.mpsnl import MPStructureNL, SNLGroup
from pymatgen.symmetry.finder import SymmetryFinder
from pymatgen.analysis.structure_matcher import StructureMatcher, ElementComparator, SpeciesComparator

sma = SNLMongoAdapter.auto_load()
matcher = StructureMatcher(
    ltol=0.2, stol=0.3, angle_tol=5, primitive_cell=True, scale=True,
    attempt_supercell=False, comparator=ElementComparator()
)

def check_snl_spacegroups(args):
    """check spacegroups of all available SNLs"""
    id_range = {"$gt": args.start, "$lte": args.end}
    mpsnl_cursor = sma.snl.find({ "snl_id": id_range})
    for mpsnl_dict in mpsnl_cursor:
        mpsnl = MPStructureNL.from_dict(mpsnl_dict)
        sf = SymmetryFinder(mpsnl.structure, symprec=0.1)
        print 'snl_id = %d: %d %d' % (
            mpsnl_dict['snl_id'], mpsnl.sg_num, sf.get_spacegroup_number()
        )

def check_snls_in_snlgroups(args):
    """check whether SNLs in each SNLGroup still match resp. canonical SNL"""
    id_range = {"$gt": args.start, "$lte": args.end}
    snlgrp_cursor = sma.snlgroups.find({ "snlgroup_id": id_range})
    for snlgrp_dict in snlgrp_cursor:
        snlgrp = SNLGroup.from_dict(snlgrp_dict)
        print snlgrp.all_snl_ids
        for snl_id in snlgrp.all_snl_ids:
            if snl_id == snlgrp.canonical_snl.snl_id or \
               len(snlgrp.all_snl_ids) <= 1: # TODO: add num_snl attribute in SNLGroup
                continue
            mpsnl_dict = sma.snl.find_one({ "snl_id": snl_id })
            mpsnl = MPStructureNL.from_dict(mpsnl_dict)
            print 'snl_id = %d: %d' % (
                snl_id, matcher.fit(mpsnl.structure, snlgrp.canonical_structure)
            )

def crosscheck_canonical_snls(args):
    """check whether canonical SNLs of two different SNL groups match"""
    snlgrp_dict1 = sma.snlgroups.find_one({ "snlgroup_id": args.primary })
    snlgrp1 = SNLGroup.from_dict(snlgrp_dict1)
    for id2 in range(args.secondary_start, args.secondary_end):
        snlgrp_dict2 = sma.snlgroups.find_one({ "snlgroup_id": id2 })
        snlgrp2 = SNLGroup.from_dict(snlgrp_dict2)
        # check composition AND spacegroup via snlgroup_key
        # TODO: add snlgroup_key attribute to SNLGroup for convenience
        if snlgrp1.canonical_snl.snlgroup_key != snlgrp2.canonical_snl.snlgroup_key:
            print('.'),
            sys.stdout.flush()
            continue
        # matcher.fit only does composition check and returns None when different compositions
        match = matcher.fit(snlgrp1.canonical_structure, snlgrp2.canonical_structure)
        print 'snlgroup_ids = (%d,%d): %d' % (args.primary, id2, match)

if __name__ == '__main__':
    # create top-level parser
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # sub-command: spacegroups
    # This task can be split in multiple parallel jobs by SNL id ranges
    parser_task0 = subparsers.add_parser('spacegroups')
    parser_task0.add_argument('--start', help='start SNL Id', default=0, type=int)
    parser_task0.add_argument('--end', help='end SNL Id', default=10, type=int)
    parser_task0.set_defaults(func=check_snl_spacegroups)

    # sub-command: groupmembers
    # This task can be split in multiple parallel jobs by SNLGroup id ranges
    parser_task1 = subparsers.add_parser('groupmembers')
    parser_task1.add_argument('--start', help='start SNLGroup Id', default=0, type=int)
    parser_task1.add_argument('--end', help='end SNLGroup Id', default=10, type=int)
    parser_task1.set_defaults(func=check_snls_in_snlgroups)

    # sub-command: canonicals
    # This task can be split in multiple parallel jobs by SNLGroup combinations
    # of (primary, secondary) ID's. The range for the secondary id always starts
    # at primary+1 (to avoid dupes)
    parser_task2 = subparsers.add_parser('canonicals')
    parser_task2.add_argument('--primary', help='primary SNLGroup Id', default=1, type=int)
    parser_task2.add_argument('--secondary-start', help='secondary start SNLGroup Id', default=10, type=int)
    parser_task2.add_argument('--secondary-end', help='secondary end SNLGroup Id', default=15, type=int)
    parser_task2.set_defaults(func=crosscheck_canonical_snls)

    # parse args and call function
    args = parser.parse_args()
    args.func(args)