import numpy as np
import numpy.ma as ma
from missMDA.svdtriplet import svdtriplet

def imputePCA(X,ncp=2,scale=True,method=['Regularized','EM'],roww=[],coeffridge=1,threshold=1e-6,seed=None,nbinit=1,maxiter=1000):

	def impute(X,mx,ncp=4,scale=True,method=None,threshold=1e-6,seed=None,init=1,maxiter=1000,roww=None,coeffridge=1):
		nbiter = 1
		old = np.inf
		objective = 0
		if seed is not None:
			np.random.seed = seed
		ncp = min(ncp,X.shape[1],X.shape[0]-1)

		means = ma.average(mx,axis=0,weights=roww).data
		Xhat = X - means
		rows = ma.masked_array(np.vstack([roww]*mx.shape[1]).T,mask=mx.mask)
		standardize = np.sqrt(np.nansum(Xhat**2*roww[:,None],axis=0)/rows.sum(axis=0))
		if scale:
			Xhat/=standardize.data
		Xhat[mx.mask]=0
		if init >1:
			Xhat[mx.mask]=np.random.randn(mx.mask.sum())
		recon = Xhat.copy()
		
		if ncp==0: 
			nbiter=0
		while nbiter>0:
			Xhat[mx.mask] = recon[mx.mask]
			if scale:
				Xhat*=standardize
			Xhat+=means
			means = np.average(Xhat,axis=0,weights=roww)
			Xhat-=means
			standardize = np.sqrt(np.nansum(Xhat**2*roww[:,None],axis=0)/roww.sum())
			if scale:
				Xhat/=standardize
			s,U,V = svdtriplet(Xhat,roww=roww)
			sigma2 = np.mean(s[ncp:]**2)
			sigma2 = min(sigma2*coeffridge,s[ncp]**2)
			if 'em' in method:
				sigma2 = 0
			lambdashrinked = (s[:ncp]**2-sigma2)/s[:ncp]
			recon = np.dot(U[:,:ncp]*roww[:,None]*lambdashrinked,V[:,:ncp].T)
			recon /= roww[:,None]
			diff = Xhat-recon
			diff[mx.mask] = 0
			objective = np.sum(diff**2*roww[:,None])
			criterion = abs(1-objective/old)
			old = objective
			nbiter +=1
			if criterion is not None:
				if criterion < threshold and nbiter > 5:
					nbiter = 0
					print "Stopped after criterion < threshold"
				if objective < threshold and nbiter > 5:
					nbiter = 0
					print "Stopped after objective < threshold"
			if nbiter > maxiter:
				nbiter = 0
				print "Stopped after " + str(maxiter) + " iterations"
		if scale:
			Xhat*=standardize
		Xhat+=means
		completeObs = X.copy()
		completeObs[mx.mask] = Xhat[mx.mask]
		if scale:
			recon*=standardize
		recon+=means
		result = [completeObs,recon]
		return result

### Impute function done now for rest of impute PCA function
	if hasattr(X,'values'):
		X = X.values.astype(float)
	elif hasattr(X,'shape'):
		X = X.astype(float)
	elif hasattr(X,'pop'):
		X = np.array(X,float)
	else:
		print "X must be a list, pandas or numpy array"
		return
	method = method[0]
	obj = np.inf
	method = method.lower()
	imputed = np.array([])
	if ncp>min(X.shape[0]-2,X.shape[1]-1):
		print "Stopping, ncp too large"
		return
	if roww == []:
		roww = np.ones(X.shape[0])/X.shape[0]
	else:
		if hasattr(roww,'pop'):
			roww = np.array(roww)
		elif hasattr(roww,'shape'):
			pass
		else:
			"roww is not a list or numpy array!"
			return
	if np.isnan(np.sum(X)):
		mx = ma.masked_array(X,mask=np.isnan(X))

	for i in range(0,nbinit):
		if ~np.isnan(np.sum(X)):
			return X
		if seed != None:
			seed=seed*i
		else:
			seed = None
		imputeit = impute(X,mx=mx,ncp=ncp,scale=scale,method=method,threshold=threshold,seed=seed,init=i+1,maxiter=maxiter,roww=roww,coeffridge=coeffridge)
		if np.mean((imputeit[1][~mx.mask]-X[~mx.mask])**2) <obj:
			imputed = imputeit
			obj = np.mean((imputeit[1][~mx.mask]-X[~mx.mask])**2)
	return imputed