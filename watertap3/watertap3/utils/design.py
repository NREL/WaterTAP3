from . import module_import
from .constituent_removal_water_recovery import create
from .mixer_wt3 import Mixer
from .source_wt3 import Source

__all__ = ['add_unit_process',
           'add_water_source',
           ]


def add_unit_process(m=None, unit_process_name=None, unit_process_type=None, unit_process_kind=None):

    up_module = module_import.get_module(unit_process_type)

    unit_params = m.fs.pfd_dict[unit_process_name]['Parameter']

    if unit_process_type == 'basic_unit':
        setattr(m.fs, unit_process_name, up_module.UnitProcess(default={'property_package': m.fs.water}))
        basic_unit_name = unit_params['unit_process_name']
        m = create(m, basic_unit_name, unit_process_name)

    else:
        setattr(m.fs, unit_process_name, up_module.UnitProcess(default={'property_package': m.fs.water}))
        m = create(m, unit_process_type, unit_process_name)

    unit = getattr(m.fs, unit_process_name)
    unit.unit_type = unit_process_type
    unit.unit_name = unit_process_name
    unit.unit_pretty_name = unit_process_name.replace('_', ' ').title().replace('Ro', 'RO').replace('Zld', 'ZLD').replace('Aop', 'AOP').replace('Uv', 'UV').replace('And', '&').replace('Sw', 'SW').replace('Gac', 'GAC').replace('Ph', 'pH').replace('Bc', 'BC').replace('Wwtp', 'WWTP')
    unit.unit_kind = unit_process_kind
    if isinstance(unit_params, float):
        unit_params = {}
    unit.unit_params = unit_params
    unit.get_costing(unit_params=unit_params)

    return m

def add_water_source(m=None, source_name=None, water_type=None, flow=None, link_to=None):
    setattr(m.fs, source_name, Source(default={'property_package': m.fs.water}))
    getattr(m.fs, source_name).set_source()
    getattr(m.fs, source_name).flow_vol_in.fix(flow)
    temp_source_df = m.fs.source_df[m.fs.source_df.water_type == water_type].copy()
    train_constituent_list = list(getattr(m.fs, source_name).config.property_package.component_list)
    for constituent_name in train_constituent_list:
        if constituent_name in temp_source_df.index:
            conc = temp_source_df.loc[constituent_name].value
            getattr(m.fs, source_name).conc_mass_in[:, constituent_name].fix(conc)
        else:
            getattr(m.fs, source_name).conc_mass_in[:, constituent_name].fix(0)

    getattr(m.fs, source_name).pressure_in.fix(1)
    return m
