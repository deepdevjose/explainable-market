"""Return forecasts with chronological calibration and expanding walk-forward tests.

NumPy/XGBoost are optional worker dependencies, never imported by the web process.
The evaluation is a limited historical experiment, not independent validation.
"""
import math
from decimal import Decimal

FEATURES = ['return_1','return_2','mean_return_5','mean_return_20','volatility_20','distance_sma_20']
VERSION = 'daily-returns-v1'
MODELS = ('persistence','ridge_ar','xgboost')


def features(prices):
    import numpy as np
    p = np.asarray(prices,dtype=float)
    if not np.all(np.isfinite(p)) or np.any(p<=0):
        raise ValueError('Positive finite prices required')
    returns = p[1:]/p[:-1]-1
    matrix = []
    for i in range(20,len(p)):
        r = returns[:i]  # Nothing beyond this observation enters the row.
        matrix.append([r[-1],r[-2],r[-5:].mean(),r[-20:].mean(),r[-20:].std(),p[i]/p[i-19:i+1].mean()-1])
    return np.asarray(matrix),returns[20:]


def fit_predict(model, x, y, row, *, explain=False):
    import numpy as np
    if model=='persistence':
        return 0., {'bias':0.,'contributions':[0.]*len(FEATURES)}
    if model=='ridge_ar':
        mean, scale = x.mean(axis=0),x.std(axis=0)
        scale = np.where(scale<1e-12,1.,scale)
        design = np.column_stack([np.ones(len(x)),(x-mean)/scale])
        penalty = np.eye(design.shape[1])*10.
        penalty[0,0] = 0
        weights = np.linalg.solve(design.T@design+penalty,design.T@y)
        contrib = ((row-mean)/scale)*weights[1:]
        return float(weights[0]+contrib.sum()),dict(bias=float(weights[0]),contributions=contrib.tolist())
    import xgboost as xgb
    train = xgb.DMatrix(x,label=y,feature_names=FEATURES)
    booster = xgb.train({'objective':'reg:squarederror','max_depth':2,'eta':0.05,
                         'min_child_weight':10,'lambda':10,'seed':42,'nthread':1},train,num_boost_round=40)
    test = xgb.DMatrix(row.reshape(1,-1),feature_names=FEATURES)
    prediction = float(booster.predict(test)[0])
    info = {}
    if explain:
        contributions = booster.predict(test,pred_contribs=True)[0]
        info = dict(bias=float(contributions[-1]),contributions=contributions[:-1].tolist(),
                    booster_json=booster.save_raw(raw_format='json').decode())
    return prediction,info


def walk_forward(model, x, y, start, end):
    # Each forecast uses only targets known strictly before the forecast row.
    return [fit_predict(model,x[:i],y[:i],x[i])[0] for i in range(start,end)]


def generate(rows: list[dict], *, include_xgboost: bool = True) -> dict:
    import numpy as np
    if len(rows)<120:
        raise ValueError('At least 120 closed daily observations required')
    if any(rows[i]['date']>=rows[i+1]['date'] for i in range(len(rows)-1)):
        raise ValueError('Strict chronological unique sessions required')
    prices = [float(r['price']) for r in rows]
    matrix, targets = features(prices)
    x = matrix[:-1]  # Last feature row has no known target yet.
    n = len(targets)
    cal_start, test_start = int(n*.60),int(n*.80)
    if min(test_start-cal_start,n-test_start)<15:
        raise ValueError('Insufficient calibration/test observations')
    models = MODELS if include_xgboost else MODELS[:2]
    calibration = {m:np.asarray(walk_forward(m,x,targets,cal_start,test_start)) for m in models}
    scores = {m:float(np.mean(np.abs(pred-targets[cal_start:test_start]))) for m,pred in calibration.items()}
    selected = min(models,key=lambda m:scores[m])  # Selection never consults held-out tests.
    residuals = np.abs(calibration[selected]-targets[cal_start:test_start])
    quantile_index = min(len(residuals)-1,math.ceil((len(residuals)+1)*.8)-1)
    radius = float(np.sort(residuals)[quantile_index])
    evaluations = {}
    for model in models:
        pred = np.asarray(walk_forward(model,x,targets,test_start,n))
        actual = targets[test_start:]
        evaluations[model] = dict(mae_return=float(np.mean(np.abs(pred-actual))),
            rmse_return=float(np.sqrt(np.mean((pred-actual)**2))),
            directional_accuracy=float(np.mean(np.sign(pred)==np.sign(actual))),test_observations=len(pred))
        if model==selected:
            evaluations[model]['empirical_interval_coverage'] = float(np.mean(np.abs(pred-actual)<=radius))
    predicted, explanation = fit_predict(selected,x,targets,matrix[-1],explain=True)
    if not math.isfinite(predicted) or predicted<=-1:
        raise ValueError('Invalid model forecast')
    reference = Decimal(rows[-1]['price'])
    def value(ret):
        return str(reference*(1+Decimal(str(ret))))
    lower,upper = max(-.999999,predicted-radius),predicted+radius
    all_predictions = {m:fit_predict(m,x,targets,matrix[-1])[0] for m in models}
    import numpy
    libraries = {'numpy':numpy.__version__}
    if include_xgboost:
        import xgboost
        libraries['xgboost'] = xgboost.__version__
    return dict(model_version=VERSION,model=selected,reference_price=str(reference),
        data_cutoff_timestamp=rows[-1]['cutoff'],prediction_horizon='next_closed_daily_observation',
        predicted_return=predicted,predicted_value=value(predicted),
        uncertainty_interval=dict(nominal_coverage=.8,lower_return=lower,upper_return=upper,
            lower_value=value(lower),upper_value=value(upper),calibration_observations=len(residuals),
            method='expanding_walk_forward_absolute_residual_quantile',calibrated=True,
            coverage_guaranteed=False),
        data_quality=dict(status='HISTORICAL',closed_observations=len(rows),
            flags=['SMALL_SAMPLE','NOT_INDEPENDENTLY_VALIDATED','NO_CAUSAL_CLAIMS']),
        evaluation_metadata=dict(protocol='expanding_walk_forward',selection='lowest_calibration_MAE',
            training_end_session=rows[20+cal_start]['date'],
            calibration_end_session=rows[20+test_start]['date'],
            test_start_session=rows[21+test_start]['date'],test_end_session=rows[-1]['date'],
            calibration_mae=scores,held_out=evaluations),
        model_metadata=dict(features=FEATURES,libraries=libraries,seed=42,
            ridge_penalty=10,xgboost=dict(trees=40,max_depth=2,eta=.05),
            explanation=explanation,latest_features=matrix[-1].tolist(),candidate_predictions=all_predictions),
        indicators=indicators(prices))


def indicators(prices):
    import numpy as np
    p = np.asarray(prices,dtype=float)
    log_returns = np.diff(np.log(p))
    def ema(span):
        result = p[0]
        for price in p[1:]:
            result += 2/(span+1)*(price-result)
        return float(result)
    deltas = np.diff(p[-15:])
    gains,losses = np.maximum(deltas,0).mean(),np.maximum(-deltas,0).mean()
    rsi = 100.-100./(1+gains/losses) if losses else (100. if gains else 50.)
    mean,std = float(p[-20:].mean()),float(p[-20:].std())
    return dict(sma20=mean,ema20=ema(20),rsi14_simple=float(rsi),macd=ema(12)-ema(26),
                bollinger20=dict(lower=mean-2*std,middle=mean,upper=mean+2*std),
                log_return=float(log_returns[-1]),daily_log_volatility20=float(log_returns[-20:].std()))
