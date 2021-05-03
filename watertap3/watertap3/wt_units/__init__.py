# import sys
# from pathlib import Path # if you haven't already done so
# file = Path(__file__).resolve()
# parent, root = file.parent, file.parents[1]
# sys.path.append(str(root))
#
# # Additionally remove the current file's directory from sys.path
# try:
#     sys.path.remove(str(parent))
# except ValueError: # Already removed
#     pass


# from . import (agglom_stacking, alum_addition, ammonia_addition, anion_exchange, anion_exchange_epa,
#                anti_scalant_addition, backwash_solids_handling, basic_unit, brine_concentrator,
#                cartridge_filtration, cation_exchange, caustic_soda_addition, chemical_addition,
#                chlorination, co2_addition, coag_and_floc, coagulant_addition, cooling_tower,
#                crystallizer, deep_well_injection, electrodialysis_reversal, evaporation_pond,
#                ferric_chloride_addition, fixed_bed_gravity_basin, fixed_bed_pressure_vessel,
#                fluidized_bed, gac, gac_gravity, gac_pressure_vessel, heap_leaching, holding_tank,
#                hydrochloric_acid_addition, iron_and_manganese_removal, irwin_brine_management,
#                landfill, landfill_zld, lime_addition, lime_softening, media_filtration,
#                microfiltration, multi_stage_bubble_aeration, municipal_drinking,
#                nanofiltration_twb, ozone_aop, packed_tower_aeration, reverse_osmosis, ro_deep,
#                sedimentation, sodium_bisulfite_addition,
#                solution_distribution_and_recovery_plant, static_mixer, sulfuric_acid_addition,
#                surface_discharge, sw_onshore_intake, treated_storage, tri_media_filtration,
#                uv_aop, water_pumping_station, well_field, wt_unit)
#
# __all__ = ['WT3UnitProcess', 'agglom_stacking', 'alum_addition', 'ammonia_addition',
#            'anion_exchange', 'anion_exchange_epa', 'anti_scalant_addition',
#            'backwash_solids_handling', 'basic_unit', 'brine_concentrator',
#            'cartridge_filtration', 'cation_exchange', 'caustic_soda_addition', 'chemical_addition',
#            'chlorination', 'co2_addition', 'coag_and_floc', 'coagulant_addition', 'cooling_tower',
#            'crystallizer', 'deep_well_injection', 'electrodialysis_reversal', 'evaporation_pond',
#            'ferric_chloride_addition', 'fixed_bed_gravity_basin', 'fixed_bed_pressure_vessel',
#            'fluidized_bed', 'gac', 'gac_gravity', 'gac_pressure_vessel', 'heap_leaching',
#            'holding_tank', 'hydrochloric_acid_addition', 'iron_and_manganese_removal',
#            'irwin_brine_management', 'landfill', 'landfill_zld', 'lime_addition',
#            'lime_softening', 'media_filtration', 'microfiltration',
#            'multi_stage_bubble_aeration', 'municipal_drinking', 'nanofiltration_twb',
#            'ozone_aop', 'packed_tower_aeration', 'reverse_osmosis', 'ro_deep', 'sedimentation',
#            'sodium_bisulfite_addition', 'solution_distribution_and_recovery_plant',
#            'static_mixer', 'sulfuric_acid_addition', 'surface_discharge', 'sw_onshore_intake',
#            'treated_storage', 'tri_media_filtration', 'uv_aop', 'water_pumping_station',
#            'well_field']

# from . import wt_unit
# from .wt_unit import WT3UnitProcess
from . import (sw_onshore_intake, municipal_drinking)

__all__ = ['sw_onshore_intake', 'municipal_drinking']


print('this is in the __init__ file for wt_units')