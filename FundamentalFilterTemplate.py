from QuantConnect.Data.UniverseSelection import *

class BasicTemplateAlgorithm(QCAlgorithm):
    
    def __init__(self):
    # set the flag for rebalance
        self.reb = 1
    # Number of stocks to pass CoarseSelection process
        self.num_coarse = 250
    # Number of stocks 
        self.num_fine = 5
        self.symbols = None

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2014,1,1)
    # if not specified, the Backtesting EndDate would be today 
        self.SetEndDate(2018,1,1)
        
        
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        self.UniverseSettings.Resolution = Resolution.Daily
        
        self.AddUniverse(self.CoarseSelectionFunction,self.FineSelectionFunction)
        
    # Schedule the rebalance function to execute at the begining of each month
        self.Schedule.On(self.DateRules.MonthStart(self.spy), 
        self.TimeRules.AfterMarketOpen(self.spy,5), Action(self.rebalance))
        
    
    def CoarseSelectionFunction(self, coarse):
    # if the rebalance flag is not 1, return null list to save time.
        if self.reb != 1:
            return self.long
            
    # make universe selection once a month
    # drop stocks which have no fundamental data or have too low prices
        selected = [x for x in coarse if (x.HasFundamentalData) 
                    and (float(x.Price) > 5)]
        
        sortedByDollarVolume = sorted(selected, key=lambda x: x.DollarVolume, reverse=True) 
        top = sortedByDollarVolume[:self.num_coarse]
        return [i.Symbol for i in top]

    def FineSelectionFunction(self, fine):
    # return null list if it's not time to rebalance
        if self.reb != 1:
            return self.long
            
        self.reb = 0
    
        filtered_fine = [x for x in fine if x.OperationRatios.OperationMargin.Value
                                        and x.ValuationRatios.PriceChange1M
                                        and x.ValuationRatios.BookValuePerShare]
                                        
        self.Log('remained to select %d'%(len(filtered_fine)))
        
        # rank stocks by three factor.
        sortedByfactor1 = sorted(filtered_fine, key=lambda x: x.OperationRatios.OperationMargin.Value, reverse=True)
        sortedByfactor2 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.PriceChange1M, reverse=True)
        sortedByfactor3 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.BookValuePerShare, reverse=True)
        
        stock_dict = {}
        
        # assign a score to each stock
        for i,ele in enumerate(sortedByfactor1):
            rank1 = i
            rank2 = sortedByfactor2.index(ele)
            rank3 = sortedByfactor3.index(ele)
            score = sum([rank1*0.2,rank2*0.2,rank3*0.6])
            stock_dict[ele] = score
        
        # sort the stocks by their scores
        self.sorted_stock = sorted(stock_dict.items(), key=lambda d:d[1],reverse=False)
        sorted_symbol = [x[0] for x in self.sorted_stock]

        # store the top stocks into the long
        self.long = [x.Symbol for x in sorted_symbol[:self.num_fine]]
        return self.long

    def OnData(self, data):
        pass
    
    def rebalance(self):
        self.Liquidate()
        
    # Equal Allocation method
        for i in self.long:
            self.SetHoldings(i, 1/self.num_fine)
        
        self.long = []
        self.reb = 1
