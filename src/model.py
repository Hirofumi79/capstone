
import joblib
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error
import numpy as np
import pandas as pd
import time
from .log_helper import *
import logging
import matplotlib.pyplot as plt
import os
import sys
import argparse
plt.style.use('seaborn')

@log_timing
def fetch_data(data_file):
    logging.info('Fetchning {}'.format(data_file))
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    logging.info('Successfully fetched {} rows and {} columns of data'.format(df.shape[0], df.shape[0]))
    return df['price'].values

@log_timing
def train_model(X, model_name):
    setup_logging('output/logs/{}_train.log'.format(model_name))
    logging.info('Splitting train-test data by 50%, incrementally adding data from test into train')
    size = int(len(X) * 0.5)
    train, test = X[0:size], X[size:len(X)]

    logging.info('Training model to predict the next time step ...')
    predictions = list()
    history = [x for x in train]
    uls = list()
    lls = list()
    for t in range(len(test)):
        model = ARIMA(history, order=(5,1,0))
        model_fit = model.fit(disp=0)
        output = model_fit.forecast()
        yhat = output[0]
        lls.append(output[2][0][0])
        uls.append(output[2][0][1])
        predictions.append(yhat)
        obs = test[t]
        history.append(obs)
        logging.info('predicted=%f, expected=%f' % (yhat, obs))
    error = mean_squared_error(test, predictions)
    logging.info('Test MSE: %.3f' % error)

    plt.figure()
    plt.title('Prediction plot (predicting the next time step)')
    plt.plot(test)
    plt.plot(predictions, color='red')
    plt.plot(uls, color='gray')
    plt.plot(lls, color='gray')
    plot_path = os.path.join('output', 'plots', model_name+'_plot.png')
    plt.savefig(plot_path)
    logging.info('Saved plot {}'.format(plot_path))
    
    # Train final model
    arima = ARIMA(X, order=(5,1,0))
    model = arima.fit(disp=0)
    model_path = os.path.join('models', model_name)
    joblib.dump(model, model_path+'.joblib')
    logging.info('Saved model {}'.format(plot_path))
    return error
    
@log_timing
def predict_model(horizon, model_name):
    setup_logging('output/logs/{}_predict.log'.format(model_name))
    t_ = time.time()
    
    model_path = os.path.join('models', model_name+'.joblib')
    if not os.path.exists(model_path):
        logging.error('Model file does not exist!')
        return None
    logging.info('Loading  model {}'.format(model_path))
    model = joblib.load(model_path)
    
    y_pred = model.forecast(horizon)[0]
    
    runtime = time.time() - t_
    logging.info('Model: {} Prediction: {} Runtime: {} Horizon: {}'.format(model_name, y_pred, runtime, horizon))
    
    return y_pred
    

if __name__ == "__main__":
    # Read arguments
    t_ = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('-country', type=str, required=True)
    args = vars(parser.parse_args())
    
    data_path = 'data/intermediate/clean_train_data_' + args['country'] + '.csv'
    model_name = 'model_'+args['country']
    
    X = fetch_data(data_path)
    train_model(X, model_name)
    predict(5, model_name)
