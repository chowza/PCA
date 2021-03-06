import numpy as np
import numpy.ma as ma
from missMDA.imputePCA import imputePCA

def estim_ncpPCA(X,ncpmin=0,ncpmax=5,method='regularized',scale=True,cv='gcv',nbsim=100,pNA=0.05,threshold=1e-4):

	if hasattr(X,'values'):
		X = X.values.astype(float)
	elif hasattr(X,'shape'):
		X = X.astype(float)
	elif hasattr(X,'pop'):
		X = np.array(X,float)
	else:
		print "X must be a list, pandas or numpy array"
		return
	
	method = method.lower()
	cv = cv.lower()
	Xhat = np.array([],float)
	ncpmax = min(ncpmax,X.shape[1]-1,X.shape[0]-2)
	result = []
	
	if cv=='gcv':
		p = X.shape[1]
		n = X.shape[0]
		if ncpmax is None:
			ncpmax = X.shape[1]-1
		ncpmax = min(X.shape[0]-2,X.shape[1]-1,ncpmax)
		crit = []
		if ncpmin == 0:
			mx = ma.masked_array(X,mask=np.isnan(X))
			crit.append(np.mean((mx - np.hstack([[np.mean(mx,axis=0).data]*X.shape[0]]))**2))


		for q in range(max(ncpmin,1),ncpmax+1):
			rec = imputePCA(X,scale=scale,ncp=q,method=method,maxiter=1000)[1]

			crit.append(np.mean(((n*p - mx.mask.sum())*(mx-rec)/((n-1)*p - mx.mask.sum() - q*(n+p-q-1)))**2))
		
		ncp = None
		if np.any(np.ediff1d(crit)>0):
			ncp = np.argmax(np.ediff1d(crit)>0)
		else:
			ncp = np.argmin(crit)
		return [ncp,crit]
		
	if cv =='loo':
		res = []
		for nbaxes in range(ncpmin,ncpmax+1):
			Xhat = ma.masked_array(X,copy=True,mask=np.isnan(X))

			it = np.nditer(X,flags=['multi_index'])
			while not it.finished:
				if ~np.isnan(X[it.multi_index[0],it.multi_index[1]]):
					mXNA = ma.masked_array(X,copy=True,mask=np.isnan(X))
					mXNA.mask[it.multi_index[0],it.multi_index[1]]=True
					mXNA.data[it.multi_index[0],it.multi_index[1]]=None
					if nbaxes==0:
						Xhat[it.multi_index[0],it.multi_index[1]] = ma.mean(mXNA[:,it.multi_index[1]])
					else:
						Xhat[it.multi_index[0],it.multi_index[1]] = imputePCA(mXNA.data,ncp=nbaxes,threshold=threshold,method=method,scale=scale)[0][it.multi_index[0],it.multi_index[1]]
				it.iternext()
			res.append(((Xhat-X)**2).mean())
		result = [np.argmin(res)+ncpmin,res]


	if cv == 'kfold':
		res = np.empty((ncpmax-ncpmin+1,nbsim))
		for sim in range(1,nbsim):
			mXNA = ma.masked_array(X,copy=True,mask=np.isnan(X))
			rowsRandom = np.random.random_integers(0,mXNA.shape[0]-1,mXNA.shape[0])
			colsRandom = np.random.random_integers(0,mXNA.shape[1]-1,mXNA.shape[0])
			mXNA.mask[[rowsRandom,colsRandom]]=True
			mXNA.data[[rowsRandom,colsRandom]]=None
			for nbaxes in range(ncpmin,ncpmax+1):
				if nbaxes==0:
					Xhat=mXNA.filled(mXNA.mean(axis=0))
				else:
					Xhat = imputePCA(mXNA.data,ncp=nbaxes,threshold=threshold,method=method,scale=scale)[0]
				res[nbaxes-ncpmin,sim] = np.nansum((Xhat-X)**2)
		resmeans = res.mean(axis=1)
		result = [np.argmin(resmeans)+ncpmin,resmeans]
	return result