import pandas as pd

def pseudo_labels(predictions, threshold=.1):
    """
    Given predictions, extract pseudo-labels
    """
    pseudo_y = predictions[(predictions.radiant_win_prob > (1 - threshold)) | (predictions.radiant_win_prob < threshold)]
    
    return pseudo_y.radiant_win_prob.map(lambda x: False if x < .5 else True)

def pseudo_enhance(X, Y, X_test, predictions, threshold=.1):
    """
    Enhance training dataset with confident samples from the test dataset, according to predictions
    
    X: train_features
    Y: train_targets
    X_test: test_features
    predictions: csv of predictions
    threshold: probability of class confidence threshold
    """
    pseudo_targets = pseudo_labels(predictions, threshold)
    
    pseudo_X = X_test.loc[pseudo_targets.index, :]
    
    return pd.concat([X, pseudo_X]), pd.DataFrame(pd.concat([Y.radiant_win, pseudo_targets]), columns=['radiant_win'])

def average_predictions(*args):
    n = len(args)
    
    accumulator = pd.read_csv(args[0], index_col=0)
    for arg in args[1:]:
        accumulator.radiant_win_prob += pd.read_csv(arg, index_col=0).radiant_win_prob
    accumulator.radiant_win_prob /= n
    return accumulator

def temperature_sharpen(*args, t=.5):
    """
    This works only for binary classification
    """
    n = len(args)
    
    accumulator = pd.read_csv(args[0], index_col=0)
    for arg in args[1:]:
        accumulator.radiant_win_prob += pd.read_csv(arg, index_col=0).radiant_win_prob ** t
    accumulator.radiant_win_prob /= n
    return accumulator

def correct_temperature_sharpen(*args, t=.5):
    """
    https://medium.com/@sshleifer/mixmatch-paper-summary-1995f3d11cf
    """
    n = len(args)
    accum = pd.read_csv(args[0], index_col=0)
    for arg in args[1:]:
        accum.radiant_win_prob += pd.read_csv(arg, index_col=0).radiant_win_prob ** (1 / t)
    accum.radiant_win_prob /= accum.radiant_win_prob.sum(axis=1)
    return accum