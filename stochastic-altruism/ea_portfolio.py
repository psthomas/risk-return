# -*- coding: utf-8 -*-
"""
Created on Wed Aug 24 20:16:53 2016

@author: dan
"""

import numpy as np

import matplotlib.pyplot as plt
#import matplotlib.patches as mpatches
#from matplotlib.patches import Ellipse
plt.style.use('ggplot')

#import random

#import cvxopt as opt
#from cvxopt import solvers
#solvers.options['show_progress'] = False

import pandas as pd

from scipy.spatial import ConvexHull

'''
def portfolio_solver(S, p=np.empty(0), r=0.0):
    n = S.shape[0]    
    
    # quadratic solver inputs
    P = 2.0*opt.matrix(S)
    q = opt.matrix(0.0, (n, 1))
    
    # inequality constraints
    G = -opt.matrix(np.eye(n))   # negative n x n identity matrix
    h = opt.matrix(0.0, (n, 1))
    
    # equality constrations
    if p.size == n:
        A = opt.matrix(np.vstack((p, np.ones((1, n)))), (2, n))
        b = opt.matrix([r, 1.0])
    # minimum variance portfolio
    else:
        A = opt.matrix(1.0, (1, n))
        b = opt.matrix(1.0)
    
    # solver
    ret = solvers.qp(P, q, G, h, A, b)   
    
    if ret['status'] == 'optimal':
        return np.array(ret['x'])
    else:
        return np.empty(0)
'''
def downside_risk(x, t):
    return np.sqrt((np.minimum(0.0, x - t)**2).sum()/x.size)

if __name__ == '__main__':
    gw_data = pd.read_pickle('gw_data.pickle')
    ace_data = pd.read_pickle('ace_data.pickle')
    fhi_data = pd.read_pickle('fhi_data.pickle')
    lead_data = pd.read_pickle('lead_data.pickle')
    
    data = pd.concat([gw_data, ace_data], axis=1)
    data = pd.concat([data, fhi_data], axis=1)
    colors = {}
    for i, j in zip(data.columns, plt.cm.jet(np.linspace(0.0, 1.0, data.shape[1]))):
        colors[i] = j
    
    data = pd.concat([data, lead_data], axis=1)
    colors['lead'] = 'gray'

    # print(data.head())
    # print(list(data.columns))
    # import sys
    # sys.exit(0)
    
    #charities = ['dtw', 'sci', 'ss', 'cash', 'bednets', 'smc', 'ads', 'leaflets', 'lead']
    charities = list(data.columns)
    n = len(charities)
    N = 10000
    
    t = data['bednets'].median()
    
    # individual returns
    p = data[charities].mean().as_matrix()
    #t = np.min(p)
    s = data[charities].apply(lambda x: downside_risk(x, t), axis=0).as_matrix()
    #s = data.std().as_matrix()
    
    # random portfolios
    #x = np.random.random([N, n])
    #x = np.divide(x, np.sum(x, axis=1).reshape(N, 1))
    x = np.random.dirichlet(np.ones(n)/2.5, N)
    
    # portfolio returns
    r = np.zeros(N)
    v = np.zeros(N)
    for j in range(N):
        d = data[charities].dot(x[j]).as_matrix()
        r[j] = np.mean(d)
        v[j] = downside_risk(d, t)
        #v[j] = np.std(d)
        
    # optimal portfolios
    hull = ConvexHull(np.vstack((v, r)).transpose())
    vm = v[hull.vertices]
    rm = r[hull.vertices]
    im0 = np.argmin(vm)
    im1 = np.argmax(rm)
    xm = x[hull.vertices][im0]
    
    # tangent portfolio
    sr = (rm - 0.0)/vm
    it = np.argmax(sr)
    vt = v[hull.vertices][it]
    rt = r[hull.vertices][it]
    xt = x[hull.vertices][it]
    
    #plt.rc('axes', prop_cycle=(cycler('color', colors)))
    
    plt.figure(0, figsize=(10, 7))  #8,6
    plt.axis([0.0, np.max(s)*1.1, 0.0, np.max(p)*1.1])
    #plt.axis([0.0, 10.0, 0.0, np.max(p)*1.1])
    plt.plot(v, r, '.', color='k', alpha=0.01)
    #plt.plot([0, vt], [0.0, rt], 'k-', label='tangency')
    #plt.plot(vm[im1:im0+1], rm[im1:im0+1], 'k-', label='optimal')
    plt.plot(vm[im0], rm[im0], 'wo', label='mvp', markersize=10)
    for j in range(n):
        c = charities[j]
        plt.plot(s[j], p[j], 'o', label=c, color=colors[c], markersize=10)
    
    
    #plt.legend(loc='best', ncol=3, numpoints=1)
    # Shrink current axis by 20% for larger legend
    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.77, box.height]) #0.8  
    plt.legend(numpoints=1, loc='center left', bbox_to_anchor=(1, 0.5)) #ncol=3,
    plt.title('Charity portfolios')
    plt.xlabel('Downside risk')
    plt.ylabel('Cost effectiveness')

    #plt.savefig('frontier.png')

    
    plt.figure(1, figsize=(10, 7))
    plt.axis('equal')
    patches, texts = plt.pie(xm, startangle=90, colors=[colors[o] for o in charities])
    #plt.legend(patches, labels=['{} ({:2.1%})'.format(charities[i], xm[i]) for i in range(n)], loc='best')
    # Shrink current axis by 20% for legend
    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.77, box.height])
    labels=['{} ({:2.1%})'.format(charities[i], xm[i]) for i in range(n)] #Eliminates arguments warning
    plt.legend(patches, labels, loc='center left', bbox_to_anchor=(1, 0.5))
    plt.title('Minimum variance portfolio')

    #plt.savefig('portfolio.png')
    
    plt.figure(2, figsize=(10, 7))
    x = np.linspace(0.0, 25.0, 100)
    for c in charities:
        yh, xh = np.histogram(data[c], bins=x, density=True)    
        plt.plot((xh[:-1] + xh[1:])/2.0, yh, label=c, color=colors[c], linewidth=2.0)
    plt.xlim([np.min(x), np.max(x)])
    plt.ylim([0.0, 1.0/3.0])
    plt.xlabel('Cost effectiveness')
    plt.ylabel('Probability')
    plt.title('PDF of cost effectiveness')

    # Shrink current axis by 20% for legend
    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.77, box.height])
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5)) #,loc='center left' loc='best'

    #plt.savefig('distributions.png')
    
    '''
    nf = 5
    tf = np.linspace(0.0, 1.0, nf)    
    fig, ax = plt.subplots(1, nf, figsize=(8, 2))
    fig.suptitle("Tangency portfolios, varying Cash", fontsize="x-large")
    for j in range(nf):
        xtf = np.append((xm*tf[j]), (1.0 - tf[j]))
        patches = ax[j].pie(xtf, colors=colors, startangle=90)  
        ax[j].axis('equal')
        ax[j].set_xlabel('{:2.1%}'.format(1.0 - tf[j]))
    
    '''
    plt.show() 