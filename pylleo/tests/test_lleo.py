

if __name__ == '__main__':
    import os

    from pylleo.pylleo import lleoio

    # TODO finish test dataset
    base_path = ('/home/ryan/Desktop/edu/01_PhD/projects/smartmove/data/'
                 'lleo_coexist/Acceleration/')
    #exp_path = ('20150311_W190-PD3GT_34839_Skinny_Control')
    #exp_path = ('20150317_W190PD3GT_34839_Skinny_4Floats')
    exp_path = ('20160418_W190PD3GT_34840_Skinny_2Neutral')
    data_path = os.path.join(base_path, exp_path)

    tag_model = 'W190PD3GT'
    tag_id    = '34840'

    meta = lleoio.read_meta(data_path, tag_model, tag_id)
    acc, depth, prop, temp = lleoio.read_data(meta, data_path, sample_f=20)
