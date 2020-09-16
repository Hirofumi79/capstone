
import os
import sys
import argparse
import logging
import pandas as pd
from log_helper import *
import time

DATA_DIR = os.path.join('..', 'data', 'source', 'cs-train')

COUNTRY_SCOPE = [
    'United Kingdom',
    'EIRE',
    'Germany',
    'France',
    'Norway',
    'Spain',
    'Hong Kong',
    'Portugal',
    'Singapore',
    'Netherlands'
]

@log_timing
def ingest_json_data(data_dir: str, country_scope: list = None) -> pd.DataFrame:
    dfs = list()
    i = 0
    for file in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file)
        if not file_path.endswith('.json'):
            continue
        try:
            df = pd.read_json(file_path)
            df.columns = [c.lower().replace('_', '') for c in df.columns]
            df = df.rename(columns={'totalprice': 'price'})
            df = df.sort_index(axis=1)
            assert all(c in df.columns for c in ['country', 'customerid', 'day', 
                 'invoice', 'month', 'price', 'streamid', 'timesviewed', 'year'])
            dfs.append(df)
        except Exception as e:
            logging.error('Failed reading {}'.format(file_path))
        else:
            logging.info('Successfully read {}, {} rows'.format(file_path, df.shape[0]))
            i += 1
        
    full_df = pd.concat(dfs).reset_index(drop=True)
    
    # Drop countries not in scope
    if country_scope:
        full_df = full_df.loc[full_df['country'].isin(country_scope)]
    
    if full_df.shape[0] == 0:
        logging.warning('Ingested data is empty')
        return None
    
    logging.info('Successfully ingested {} files, {} total rows'.format(i, full_df.shape[0]))
    return full_df

@log_timing
def process_data(df):
    df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-' + df['day'].astype(str))
    df = df.drop(columns=['customerid'])
    df = df.groupby('country').resample('W', on='date').sum().reset_index()    
    return df
    
@log_timing
def export_data(target_file, df_clean, overwrite=False, groupby=None):
    if groupby:
        for g, dfg in df_clean.groupby(groupby):
            export_data(target_file+'_'+g, dfg, overwrite)
    else:
        if overwrite or not os.path.exists(target_file):
            df_clean.to_csv(target_file+'.csv', index=False)   
            logging.info('Successfully overwrote output to {}'.format(target_file))
        else:
            df_clean.to_csv(target_file+'.csv', mode='a', header=False, index=False)
            logging.info('Successfully wrote output to {}'.format(target_file))
        
    
if __name__ == "__main__":
    setup_logging('../output/logs/ingestion.log')
    # Read arguments
    t_ = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('-output', type=str, required=True)
    args = vars(parser.parse_args())
    
    df = ingest_json_data(DATA_DIR)
    if df is None:
        sys.exit(1)

    df = process_data(df)
    
    export_data(args['output'], df, overwrite=False, groupby='country')
    logging.info('Data ingestion complete, runtime {} sec'.format(time.time()-t_))
