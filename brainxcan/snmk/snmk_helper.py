from collections import OrderedDict

import brainxcan.snmk.default_params as default_params
import brainxcan.snmk._snmk_helper as sh


# def aggregate_chkpnt(wildcards):
#     '''
#     aggregate the files generated by checkpoint sbxcan_signif
#     '''
#     checkpoint_output = checkpoints.sbxcan_signif.get(**wildcards).output[0]
#     return expand('{outdir}/{prefix}.{idp_name}.MR_vis.png',
#            idp_name=glob_wildcards(os.path.join(checkpoint_output, '{idp_name}.txt')).idp_name)

def check_required_args(config):
    required = ['gwas', 'datadir', 'chr', 'non_effect_allele', 'effect_allele', 'snpid', 'prefix', 'brainxcan_path']
    sh._check_list_all_in(required, config)

def fill_spearman_cutoff(config):
    sh._try_fill_config(config, 'spearman_cutoff', default_params.SPEARMAN_CUTOFF)
    return config['spearman_cutoff']

def fill_gwas_col_meta(config):
    '''
    snpid: 'rsid'
    effect_allele: 'effect_allele'
    non_effect_allele: 'non_effect_allele'
    effect_size: 'effect_size'
    effect_size_se: 'standard_error'
    chr: 'chromosome'
    zscore: 'zscore'
    sample_size: 'sample_size'
    allele_frequency: 'frequency'
    '''
    key_map_to_mr = {
        'snpid': 'variant_id',
        'effect_size_se': 'se',
        'allele_frequency': 'af'
    }
    main_cols = ['snpid', 'effect_allele', 'non_effect_allele', 'chr']
    desired_cols_b = [ 
        'effect_size', 'effect_size_se'
    ]
    desired_cols_z = [
        'zscore', 'sample_size', 'allele_frequency'
    ]
    # check main cols
    for k in main_cols:
        if k not in config:
            raise ValueError(f'We require {k} to load GWAS.')
    modes = [ 'bhat', 'zscore' ]
    mode = modes[ sh._decide_mode(desired_cols_b, desired_cols_z, config) ]
    if mode == 'bhat':
        cols = main_cols + desired_cols_b
    elif mode == 'zscore':
        cols = main_cols + desired_cols_z
    
    bxcan_key_val_pairs = []
    mr_key_val_pairs = []
    for cc in cols:
        bxcan_key_val_pairs.append('{}:{}'.format(cc, config[cc]))
        if cc in key_map_to_mr:
            cc_mr = key_map_to_mr[cc]
        else:
            cc_mr = cc
        mr_key_val_pairs.append('{}:{}'.format(config[cc], cc_mr))
    return ' '.join(bxcan_key_val_pairs), ','.join(mr_key_val_pairs)

def fill_sbxcan_signif_criteria(config):
    sh._fill_config_w_default_if_needed(config, default_params.BXCAN_SIGNIF)
    config['signif_pval'] = float(config['signif_pval'])
    config['signif_max_idps'] = int(config['signif_max_idps'])
    if config['signif_pval'] > 1 or config['signif_pval'] <= 0:
        raise ValueError('P-value cutoff should be in (0, 1].')
    if config['signif_max_idps'] < 0:
        raise ValueError('Cannot be negative.')
    arg = '--pval {} --max_idps {}'.format(
        config['signif_pval'], config['signif_max_idps']
    )
    return arg, config['signif_max_idps']

def fill_sbxcan_idp_weight(config):
    t1 = sh._try_to_format(
        config['idp_weights_pattern'],
        OrderedDict([
            ('datadir', config['datadir']), 
            ('idp_type', config['idp_type']),
            ('model_type', config['model_type']),
            ('idp_modality', 't1') 
        ])
    ) 
    t1 = [ t1, sh._parquet2perf(t1) ]
    dmri = sh._try_to_format(
        config['idp_weights_pattern'],
        OrderedDict([
            ('datadir', config['datadir']), 
            ('idp_type', config['idp_type']),
            ('model_type', config['model_type']),
            ('idp_modality', 'dmri') 
        ])
    )     
    dmri = [ dmri, sh._parquet2perf(dmri) ]
    cols = [ f'{k}:{v}' for k, v in config['idp_weights_cols'].items() ]
    return cols, t1, dmri  
    
def check_datadir(config):
    if 'datadir' not in config:
        raise ValueError('Need to specify the datadir.')
        
def fill_idp_type(config):
    sh._try_fill_config(
        config, 'idp_type', 
        default_params.IDP_TYPE[0], default_params.IDP_TYPE[1]
    )

def fill_model_type(config):
    sh._try_fill_config(
        config, 'model_type', 
        default_params.MODEL_TYPE[0], default_params.MODEL_TYPE[1]
    )

def fill_sbxcan_geno_cov(config):
    files = sh._try_format_for_list(
        config['geno_cov_pattern'],
        OrderedDict([('datadir', config['datadir'])]),
        default_params.CHRS, 'chr_num'
    )
    arg = sh._try_to_format(
        config['geno_cov_pattern'], 
        OrderedDict([('datadir', config['datadir'])])
    )
    return arg, files
    
def fill_patterns(config):
    sh._try_fill_config(config, 'geno_cov_pattern', default_params.GENO_COV_PATTERN)
    sh._try_fill_config(config, 'idp_weights_pattern', default_params.IDP_WEIGHTS_PATTERN)
    sh._try_fill_config(config, 'idp_weights_cols', default_params.IDP_WEIGHTS_COLS)
    sh._check_desired_wildcards(
        config['geno_cov_pattern'], [ '{chr_num}' ]
    )
    sh._check_desired_wildcards(
        config['idp_weights_pattern'], [ '{idp_modality}' ]
    )
    sh._check_list_all_in(
        list(default_params.IDP_WEIGHTS_COLS.keys()),
        config['idp_weights_cols']
    )
    config['idp_weights_pattern'] = sh._try_to_format(
        config['idp_weights_pattern'], 
        OrderedDict([
            ('datadir', config['datadir']),
            ('idp_type', config['idp_type']),
            ('model_type', config['model_type'])
        ])
    )
def fill_exe(config):
    sh._try_fill_config(config, 'python_exe', default_params.PYTHON_EXE)
    sh._try_fill_config(config, 'rscript_exe', default_params.RSCRIPT_EXE)
    sh._try_fill_config(config, 'plink_exe', default_params.PLINK_EXE)

def fill_ld_clump_yaml(config):
    sh._try_fill_config(config, 'ld_clump_yaml', default_params.LD_CLUMP_YAML)
    config['ld_clump_yaml'] = sh._try_to_format(
        config['ld_clump_yaml'], 
        OrderedDict([('datadir', config['datadir'])])
    )
    return config['ld_clump_yaml']

def fill_gwas_idp(config):
    sh._try_fill_config(config, 'idp_gwas_pattern', default_params.IDP_GWAS_PATTERN)
    sh._check_desired_wildcards(
        config['idp_gwas_pattern'], 
        [ '{chr_num}', '{idp_code}', '{idp_modality}' ]
    )
    param = sh._try_to_format(
        config['idp_gwas_pattern'], 
        OrderedDict([
            ('datadir', config['datadir']),
            ('idp_type', config['idp_type']),
            ('chr_num', '[chr_num]')
        ])
    )
    files = sh._try_format_for_list(
        config['geno_cov_pattern'],
        OrderedDict([
            ('datadir', config['datadir']),
            ('idp_type', config['idp_type'])
        ]),
        default_params.CHRS, 'chr_num'
    )
    return param, files

def fill_snp_bim(config):
    sh._try_fill_config(config, 'idp_gwas_snp_pattern', default_params.IDP_GWAS_SNP_PATTERN)
    sh._check_desired_wildcards(
        config['idp_gwas_snp_pattern'], [ '{chr_num}' ]
    )
    arg = sh._try_to_format(
        config['idp_gwas_snp_pattern'], 
        OrderedDict([
            ('datadir', config['datadir']),
            ('chr_num', '[chr_num]')
        ])
    )
    files = sh._try_format_for_list(
        config['geno_cov_pattern'],
        OrderedDict([('datadir', config['datadir'])]),
        default_params.CHRS, 'chr_num'
    )
    return arg, files

def fill_mr_ld_panel(config):
    sh._try_fill_config(config, 'gwas_pop', default_params.GWAS_POP)
    sh._check_val_in_pool(config['gwas_pop'], default_params.GWAS_POPS)
    sh._try_fill_config(config, 'mr_ld_panel_pattern', default_params.MR_LD_PANEL_PATTERN)
    arg = sh._try_to_format(
        config['mr_ld_panel_pattern'], 
        OrderedDict([
            ('datadir', config['datadir']),
            ('gwas_pop', config['gwas_pop'])
        ])
    )
    files = sh._try_format_for_list(
        config['geno_cov_pattern'] + '.{suffix}',
        OrderedDict([
            ('datadir', config['datadir']),
            ('gwas_pop', config['gwas_pop'])
        ]),
        ['bed', 'bim', 'fam'], 'suffix'
    )
    return arg, files

def fill_bxcan_vis_datadir(config):
    sh._try_fill_config(config, 'bxcan_vis_datadir', default_params.BXCAN_VIS_DATADIR)
    res = sh._try_to_format(
        config['bxcan_vis_datadir'], 
        OrderedDict([('datadir', config['datadir'])])
    )
    return res

def fill_bxcan_report_data(config):
    sh._try_fill_config(config, 'bxcan_idp_meta', default_params.BXCAN_IDP_META)
    sh._try_fill_config(config, 'bxcan_color_code', default_params.BXCAN_COLOR_CODE)
    meta = sh._try_to_format(
        config['bxcan_idp_meta'], 
        OrderedDict([('datadir', config['datadir'])])
    )
    color = sh._try_to_format(
        config['bxcan_color_code'], 
        OrderedDict([('datadir', config['datadir'])])
    )
    return meta, color

def fill_bxcan_region_vis(config):
    sh._try_fill_config(config, 'bxcan_region_vis', default_params.BXCAN_REGION_VIS)
    if config['bxcan_region_vis'] is True:
        return '--region_vis'
    else:
        return ''
