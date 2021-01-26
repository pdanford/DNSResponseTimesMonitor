from collections import deque

# version 1.0.0
# requires Python 3.x
# pdanford - January 2021
# MIT License

class SMA:
    """
    Simple Moving Average

    Computes SMA iteratively by calling CalculateNextSMA(). The SMA is
    initialized progressively using a sample window that grows with each
    new value added until the window is the size the SMA instance was
    created with. This is so 0s are not returned while the sample window
    is being filled. I.e., shorter period averages are returned while the
    SMA is collecting enough values to return the proper SMA.
    """

    def __init__(self, sma_period):
        self.sma = 0
        self.sma_period = sma_period
        self.sample_window = deque(maxlen = sma_period)


    def GetPeriod(self):
        """
        Return SMA peried this instance was created with.
        """
        return self.sma_period


    def GetCurrentSMA(self):
        """
        Return current calculated SMA as of last CalculateNextSMA() call. This
        is the same value returned by the last CalculateNextSMA() call.
        """
        return self.sma


    def CalculateNextSMA(self, new_val):
        """
        Compute Simple Moving Average iteratively

        This uses a progressive formula to build up (i.e. initialize) the SMA
        until enough new values are added to make sample window size match
        sma_period and return the proper SMA.
        """

        if len(self.sample_window) < self.sma_period:
            # -- progressively establish new sma --
            # (i.e. use a progressive formula until we have sma_period samples)

            # add new value to sample window
            self.sample_window.append(new_val)
            # combine new value (while adjusting for sample size increasing)
            self.sma = self.sma + 1/len(self.sample_window) * (new_val - self.sma)
        else:
            # -- update established SMA --
            # add new value to sma average
            self.sma += (new_val / self.sma_period)
            # subtract leftmost value of sample window from sma
            self.sma -= (self.sample_window[0] / self.sma_period)
            # add new value to sample window
            self.sample_window.append(new_val)

        return self.sma

