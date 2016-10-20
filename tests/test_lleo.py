

if __name__ == '__main__':
    import os

    import lleo

    base_path = ('/home/ryan/Desktop/edu/01_PhD/projects/smartmove/data/'
                 'lleo_coexist/Acceleration/')
    exp_path = ('20150311_W190-PD3GT_34839_Skinny_Control')
    exp_path = ('20150317_W190PD3GT_34839_Skinny_4Floats')
    exp_path = ('20160418_W190PD3GT_34840_Skinny_2Neutral')
    data_path = os.path.join(base_path, exp_path)

    param_strs = ['Acceleration-X', 'Acceleration-Y', 'Acceleration-Z', 'Depth',
                  'Propeller', 'Temperature']

    n_header = 10

    meta = lleo.read_meta(data_path, param_strs, n_header)
    acc, depth, prop, temp = lleo.read_data(meta, data_path, n_header,
                                            sample_f=20)
