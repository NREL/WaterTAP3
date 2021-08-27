from . import module_import
from .constituent_removal_water_recovery import create
from .mixer_wt3 import Mixer
from .source_wt3 import Source

__all__ = ['add_unit_process',
           'add_water_source',
           'add_splitter',
           'add_mixer']


def add_unit_process(m=None, unit_process_name=None, unit_process_type=None, unit_process_kind=None):

    up_module = module_import.get_module(unit_process_type)

    unit_params = m.fs.pfd_dict[unit_process_name]['Parameter']

    if 'basic' in unit_process_type:
        setattr(m.fs, unit_process_name, up_module.UnitProcess(default={'property_package': m.fs.water}))
        basic_unit_name = unit_params['unit_process_name']
        m = create(m, basic_unit_name, unit_process_name)

    else:
        setattr(m.fs, unit_process_name, up_module.UnitProcess(default={'property_package': m.fs.water}))
        m = create(m, unit_process_type, unit_process_name)


    getattr(m.fs, unit_process_name).get_costing(unit_params=unit_params)
    unit = getattr(m.fs, unit_process_name)
    unit.unit_name = unit_process_name
    unit.unit_kind = unit_process_kind

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


def add_splitter(m=None, split_name=None, with_connection=False, outlet_list=None, outlet_fractions=None,
                 link_to=None, link_from=None, stream_name=None, unfix=False):

    setattr(m.fs, split_name, Separator(default={
            'property_package': m.fs.water,
            'ideal_separation': False,
            'outlet_list': outlet_list
            }))

    if unfix == True:
        getattr(m.fs, split_name).split_fraction[0, key].unfix()
    else:
        for key in outlet_fractions.keys():
            getattr(m.fs, split_name).split_fraction[0, key].fix(outlet_fractions[key])
    return m


def add_mixer(m=None, mixer_name=None, with_connection=False, inlet_list=None,
              link_to=None, link_from=None, stream_name=None):

    setattr(m.fs, mixer_name, Mixer(default={
            'property_package': m.fs.water,
            'inlet_list': inlet_list
            }))
    return m
