
__all__ = ['splitter_streams']
# goes into each unit in from units list and unfixes all the stream fractions associate with that unit
#for optimization. eventually may want to optimize particular streams if more than 2 coming out of unit.
def splitter_streams(m=None, from_units=None):
    for unit in from_units:
        for key in m.fs.arc_dict:
            if m.fs.arc_dict[key][0] == unit:
                splitter_name = m.fs.arc_dict[key][2]
                for outlet_i in getattr(m.fs,  splitter_name).outlet_list:
                    print("unfixes stream from --->", splitter_name, ("---> %s" % outlet_i))
                    getattr(getattr(m.fs,  splitter_name), ("split_fraction_%s" % outlet_i)).unfix()
    return m