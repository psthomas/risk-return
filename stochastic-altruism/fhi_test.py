
import json
import numpy as np
import pandas as pd

# "title": "Estimating the cost-effectiveness of research into neglected diseases",
# "description": "http://www.fhi.ox.ac.uk/research-into-neglected-diseases/",
# "source": "https://docs.google.com/spreadsheets/d/1yjgr0aiHTQF4i5jMy4Q-MI1TLWC6sMoS14MorZc6nNw/edit#gid=6"

def sample_fhi():
    n = 100000
    m = 1000.0

    with open('fhi_params.json') as fp:    
        params = json.load(fp)

    columns = params['data'].keys()
    samples = []

    for column in columns:
        mu = params['data'][column]['mu']
        sigma = params['data'][column]['sigma']
        sample = np.random.lognormal(mu, sigma, n)
        samples.append(sample)
        
    data = np.array(samples).transpose()
    df = pd.DataFrame(data, columns=columns)
    df.to_pickle('fhi_data.pickle')


if __name__ == "__main__":
    sample_fhi()

    