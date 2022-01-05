import pandas as pd
import pandas_ta as pta
from abc import ABC, abstractmethod
from enum import Enum

from cost_basis import CostBasis
from simple_action import Action, Action_Hold, Action_BuyAll, Action_SellAll, Action_Buy, Action_Sell, Action_Buy100, Action_Sell100

CD_NONE = 0
CD_ONE_HOUR = 3600
CD_SIX_HOUR = 21600
CD_ONE_DAY = 86400

DF_COLUMNS = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

class Agent(ABC):
    def __init__(self, fee=0) -> None:
        self._df = pd.DataFrame(columns=DF_COLUMNS)
        self._clock = None
        self._action_list = []
        self._fee = fee

    @property
    def fee_rate(self):
        return self._fee

    def set_clock(self, obj) -> None:
        self._clock = obj

    def set_action_list(self, action_list) -> None:
        self._action_list = action_list

    def update(self, df, qty_usd=None, qty_crypto=None) -> None:
        self._df = self._df.append(df, ignore_index=True)

        if qty_usd == None or qty_crypto == None:
            # If qty_usd or qty_crypto is not specified, then we either expect the dataframe
            # to be a fully complete dataframe (from a live observer) or a partially complete
            # dataframe from a play-back (ie. csv) observer, in which we'll need to "fill in"
            # the missing NaN cells.
            if pd.isna(self._df.iloc[-1]['qty_usd']):
                self._df.at[self._df.index[-1],'qty_usd'] = self._df.iloc[-2]['qty_usd']
            if pd.isna(self._df.iloc[-1]['qty_crypto']):
                self._df.at[self._df.index[-1],'qty_crypto'] = self._df.iloc[-2]['qty_crypto']
            if pd.isna(self._df.iloc[-1]['networth']):
                self._df.at[self._df.index[-1],'networth'] = self._df.iloc[-1]['qty_usd'] + (self._df.iloc[-1]['qty_crypto']*self._df.iloc[-1]['bid'])
        else:
            # If BOTH qty_usd and qty_crypto are specified, then we are simulating these cells
            # instead of fetching live data from the observer.
            self.update_tail(qty_usd, qty_crypto)

    def update_tail(self, qty_usd, qty_crypto) -> None:
        self._df.at[self._df.index[-1], 'qty_usd'] = qty_usd
        self._df.at[self._df.index[-1], 'qty_crypto'] = qty_crypto
        self._df.at[self._df.index[-1], 'networth'] = qty_usd + (qty_crypto*self._df.iloc[-1]['bid'])
    
    def reset(self) -> None:
        pass
    
    @abstractmethod
    def get_action(self) -> Action:
        pass

class HODL_Agent(Agent):
    def __init__(self, fee=0) -> None:
        super().__init__(fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_BuyAll(agent=self, cd=CD_SIX_HOUR)
        ]
        self.set_action_list(action_list)
    
    def get_action(self) -> Action:
        last_qty_usd = self._df.iloc[-1]['qty_usd']
        if last_qty_usd > 0:
            return self._action_list[1] # Buy All
        else:
            return self._action_list[0] # Hold

    def reset(self) -> None:
        return super().reset()

class DCA_Benchmark_Agent(Agent):
    def __init__(self, fee=0, days=3, qty=100) -> None:
        super().__init__(fee=fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_Buy(agent=self, cd=days*24*60*60, qty=qty)
        ]
        self.set_action_list(action_list)

        self._cost_basis = CostBasis()

    def get_cost_basis(self):
        return self._cost_basis.get_cost_basis()

    def get_action(self) -> Action:
        ask = self._df.iloc[-1]['ask']
        last_qty_usd = self._df.iloc[-1]['qty_usd']
        
        if last_qty_usd > 0 and self._action_list[1].time_til() <= 0:
            usd_to_xfer = self._action_list[1].qty if last_qty_usd >= self._action_list[1].qty else last_qty_usd
            fee_usd = usd_to_xfer * self.fee_rate
            # Record this buy so cost basis may be calculated at the end.
            self._cost_basis.buy((usd_to_xfer-fee_usd)/ask, ask)
            print(f"NEW Cost Basis: {self.get_cost_basis()}")
            return self._action_list[1] # Buy
        else:
            return self._action_list[0] # Hold

class Test_Agent(Agent):
    def __init__(self, fee=0) -> None:
        super().__init__(fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            #Action_BuyAll(agent=self, cd=CD_SIX_HOUR),
            #Action_SellAll(agent=self, cd=CD_SIX_HOUR),
            Action_Buy100(agent=self, cd=CD_ONE_HOUR),
            Action_Sell100(agent=self, cd=CD_ONE_HOUR)
        ]
        self.set_action_list(action_list)

    def update(self, df) -> None:
        super().update(df)
        self._df["SMA"] = self._df['bid'].rolling(360).mean()
        self._df["EMA"] = self._df['bid'].ewm(360).mean()
        self._df["DIFF_HR"] = self._df['bid'].diff(periods=60)
        self._df["DIFF_DAY"] = self._df['bid'].diff(periods=1440)
        self._df["PCT_HR"] = self._df['bid'].pct_change(periods=60)
        self._df["PCT_DAY"] = self._df['bid'].pct_change(periods=1440)
    
    def get_action(self) -> Action:
        bid = self._df.iloc[-1]['bid']
        ask = self._df.iloc[-1]['ask']
        last_qty_usd = self._df.iloc[-1]['qty_usd']
        last_qty_ass = self._df.iloc[-1]['qty_crypto']

        ema = self._df.at[self._df.index[-1], 'EMA']
        if (ask+ask*0.02) < ema and last_qty_usd > 0:
            return self._action_list[1] # Buy 100
        elif (bid-bid*0.02) > ema and last_qty_ass > 0:
            return self._action_list[2] # Sell 100
        else:
            return self._action_list[0] # Hold

    def reset(self) -> None:
        return super().reset()

class SMA_Agent(Agent):
    def __init__(self, fee, sma_s, sma_l) -> None:
        super().__init__(fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_BuyAll(agent=self, cd=CD_NONE),
            Action_SellAll(agent=self, cd=CD_NONE)
        ]
        self.set_action_list(action_list)
        
        # SMA short and long window period coverted from days to minutes
        self._sma_s = sma_s*24*60
        self._sma_l = sma_l*24*60

    @property
    def SMA_s(self):
        return self._sma_s

    @property
    def SMA_l(self):
        return self._sma_l

    def update(self, df) -> None:
        super().update(df)
        self._df["SMA_S"] = self._df['bid'].rolling(self.SMA_s).mean()
        self._df["SMA_L"] = self._df['bid'].rolling(self.SMA_l).mean()

    def get_action(self) -> Action:
        last_qty_usd = self._df.iloc[-1]['qty_usd']
        last_qty_ass = self._df.iloc[-1]['qty_crypto']
        sma_s = self._df.at[self._df.index[-1], 'SMA_S']
        sma_l = self._df.at[self._df.index[-1], 'SMA_L']

        sma_s_prev = self._df.at[self._df.index[-2], 'SMA_S']

        if sma_s_prev < sma_l and sma_s >= sma_l and last_qty_usd > 0:
            # Golden Cross
            return self._action_list[1] # Buy All
        elif sma_s_prev >= sma_l and sma_s < sma_l and last_qty_ass > 0:
            # Death Cross
            return self._action_list[2] # Sell All
        else:
            return self._action_list[0] # Hold

class SMA_5_20_Agent(SMA_Agent):
    def __init__(self, fee) -> None:
        super().__init__(fee, sma_s=5, sma_l=20)

    def update(self, df) -> None:
        super().update(df)

    def get_action(self) -> Action:
        return super().get_action()

class SMA_1_5_Agent(SMA_Agent):
    def __init__(self, fee) -> None:
        super().__init__(fee, sma_s=1, sma_l=5)

    def update(self, df) -> None:
        super().update(df)

    def get_action(self) -> Action:
        return super().get_action()

class RSI_Agent(Agent):
    def __init__(self, fee=0, length=14) -> None:
        super().__init__(fee=fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_Buy(agent=self, cd=CD_SIX_HOUR, qty=200),
            Action_Sell(agent=self, cd=CD_SIX_HOUR, qty=200)
        ]
        self.set_action_list(action_list)

        self._length = length

    @property
    def length(self): return self._length

    @length.setter
    def length(self, value): self._length = value

    def update(self, df) -> None:
        super().update(df)
        self._df["RSI"] = pta.rsi(self._df['bid'], length=14)

    def get_action(self) -> Action:
        last_qty_usd = self._df.at[self._df.index[-1], 'qty_usd']
        last_qty_ass = self._df.at[self._df.index[-1], 'qty_crypto']

        rsi = self._df.at[self._df.index[-1], 'RSI']

        is_overvalued = rsi > 70
        is_undervalued = rsi < 30

        if is_undervalued and last_qty_usd > 0:
            return self._action_list[1] # Buy
        elif is_overvalued and last_qty_ass > 0:
            return self._action_list[2] # Sell
        else:
            return self._action_list[0] # Hold

class DCA_Agent(Agent):

    class DCA_Agent_State(Enum):
        WAIT_FOR_ENTRY = 1
        BUYING_BELOW_ENTRY = 2
        WAIT_FOR_EXIT = 3

    def __init__(self, fee=0, base=500, tp_percent=0.02, buy_percent=0.05) -> None:
        super().__init__(fee=fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_Buy(agent=self, cd=300, qty=base),
            Action_Buy100(agent=self, cd=300),
            Action_SellAll(agent=self, cd=300),
        ]
        self.set_action_list(action_list)

        self._tp_percent = tp_percent
        self._buy_percent = buy_percent

        self._entry_price = 0
        self._next_buy_price = 0
        self._avg_buy_price = 0
        #self._break_even_price = 0
        self._take_profit_price = 0

        self._state = DCA_Agent.DCA_Agent_State.WAIT_FOR_ENTRY

    @property
    def state(self): return self._state

    @state.setter
    def state(self, value): self._state = value
    
    @property
    def entry_price(self): return self._entry_price

    @entry_price.setter
    def entry_price(self, value): self._entry_price = value

    @property
    def next_buy_price(self): return self._next_buy_price

    @next_buy_price.setter
    def next_buy_price(self, value): self._next_buy_price = value

    @property
    def avg_buy_price(self): return self._avg_buy_price

    @avg_buy_price.setter
    def avg_buy_price(self, value): self._avg_buy_price = value
    
    #@property
    #def break_even_price(self): return self._break_even_price
    
    def _get_tp_price(self):
        return self._avg_buy_price * (1 + self._tp_percent)

    def update(self, df) -> None:
        super().update(df)
        self._df["EMA"] = self._df['bid'].ewm(5).mean()
        self._df["BID_DIFF"] = self._df['bid'].diff(periods=5)
        self._df["EMA_DIFF"] = self._df['EMA'].diff(periods=5)
        self._df["RSI"] = pta.rsi(self._df['bid'], length=14)

    def get_action(self) -> Action:
        bid = self._df.at[self._df.index[-1], 'bid']
        ask = self._df.at[self._df.index[-1], 'ask']
        last_qty_usd = self._df.at[self._df.index[-1], 'qty_usd']
        last_qty_ass = self._df.at[self._df.index[-1], 'qty_crypto']

        slope_prev = self._df.at[self._df.index[-2], 'BID_DIFF']
        slope = self._df.at[self._df.index[-1], 'BID_DIFF']

        is_local_min = True if slope_prev < 0 and slope >= 0 else False
        is_local_max = True if slope_prev > 0 and slope <= 0 else False

        rsi_prev = self._df.at[self._df.index[-2], 'RSI']
        rsi = self._df.at[self._df.index[-1], 'RSI']

        is_overvalued = rsi > 70
        is_undervalued = rsi < 30

        bull_signal = True if rsi_prev < 30 and rsi >= 30 else False
        bear_signal = True if rsi_prev > 70 and rsi <= 70 else False
        
        if self.state == DCA_Agent.DCA_Agent_State.WAIT_FOR_ENTRY:
            
            if is_undervalued and last_qty_usd > 0:
                self.entry_price = ask
                self.avg_buy_price = self.entry_price
                self.next_buy_price = self.entry_price * (1 - self._buy_percent)
                self.state = DCA_Agent.DCA_Agent_State.BUYING_BELOW_ENTRY
                print(f"Entry price: {self.entry_price} USD, Initial TP: {self._get_tp_price()} USD, Next buy price: {self.next_buy_price} USD")
                return self._action_list[1] # Buy Base Qty
            else:
                return self._action_list[0] # Hold

        elif self.state == DCA_Agent.DCA_Agent_State.BUYING_BELOW_ENTRY:
            
            if ask < self.next_buy_price and last_qty_usd > 0 and self._action_list[1].time_til() <= 0:
                usd_to_xfer = 100 if last_qty_usd >= 100 else last_qty_usd
                fee_usd = usd_to_xfer * self.fee_rate
                self.avg_buy_price = (last_qty_ass * self._avg_buy_price + (((usd_to_xfer-fee_usd)/ask)*ask) ) / ( last_qty_ass + ((usd_to_xfer-fee_usd)/ask) )
                #self.avg_buy_price = (last_qty_ass * self.avg_buy_price + (usd_to_xfer-fee_usd)) / ( last_qty_ass + ((usd_to_xfer-fee_usd)/ask) )
                self.next_buy_price = ask * (1 - self._buy_percent)
                print(f"Extra buy: {ask} USD, Avg buy price: {self.avg_buy_price} USD, New TP price: {self._get_tp_price()} USD, Next buy price: {self.next_buy_price} USD")
                return self._action_list[2] # Buy 100
            elif bid > self._get_tp_price():
                print(f"Bid ({bid} USD) hit take profit threshold: {self._get_tp_price()} USD. Now waiting for exit")
                self.state = DCA_Agent.DCA_Agent_State.WAIT_FOR_EXIT
                return self._action_list[0] # Hold
            else:
                return self._action_list[0] # Hold

        elif self.state == DCA_Agent.DCA_Agent_State.WAIT_FOR_EXIT:
            bid_prev = self._df.at[self._df.index[-2], 'bid']
            if bid > self._get_tp_price() and last_qty_ass > 0 and self._action_list[2].time_til() <= 0:
                print(f"Taking profit at {bid} USD")
                self.state = DCA_Agent.DCA_Agent_State.WAIT_FOR_ENTRY
                return self._action_list[3] # Sell All, take profits
            else:
                return self._action_list[0] # Hold
