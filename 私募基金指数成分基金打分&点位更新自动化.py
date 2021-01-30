"""
私募基金指数成分基金打分&点位更新
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from WindPy import w

class hf_index_weight(): # 每半年自动调仓及成分权重
    
    def __init__(self, hf_inputfile, bm_inputfile, reset_date):
        self.raw_data = pd.read_excel(hf_inputfile)
        self.benchmark_data = pd.read_excel(bm_inputfile)
        self.hf_list = list(self.raw_data)[1:]
        self.benchmark = self.raw_data.iloc[0,1:].values.tolist()
        self.T0_set = reset_date
        for i in range(len(self.T0_set)):
            self.T0_set[i] = datetime.strptime(self.T0_set[i],"%Y-%m-%d")
        
    def Start_Wind(self):
        w.start()
        w.isconnected()
    '''
    def benchmark_index(self):
        found_date = self.found_date()
        raw_date = self.raw_data['日期'].tolist()[1:]
        bm_index_list = []
        for i in range(len(self.benchmark)):
            bm_date_id = raw_date.index(found_date[i])
            bm_date = raw_date[:bm_date_id+1]
            bm_index = []
            for j in range(len(bm_date)):
                price = w.wss("000300.SH", "close","tradeDate="+str(bm_date[j])+";priceAdj=F;cycle=D").Data[0][0]
                bm_index.append(price)
            bm_index_list.append(bm_index)
        return bm_index_list
    '''                
                
    def found_date(self):
        date_list = []
        for i in self.hf_list:
            if self.raw_data[i].isnull().any().any():
                df_nnan = self.raw_data[self.raw_data.isnull()[i] == False]
                date = df_nnan.iloc[-1,0]
            else:
                date = self.raw_data.iloc[-1,0]
            date_list.append(date)
        return date_list
    
    def annual_return(self, T0_date):
        date_list = self.found_date()
        raw_date = self.raw_data['日期'].tolist()[1:]
        T0_date_id = raw_date.index(T0_date)
        hf_return = []
        benchmark_return = []
        for i in range(len(self.hf_list)):
            if float((T0_date - date_list[i]).days) <=0:
                hf_ra = np.nan
                hf_return.append(hf_ra)
                bm_ra = np.nan
                benchmark_return.append(bm_ra)
            # 生成成分基金成立以来年化收益率
            else:
                hf_nav = self.raw_data[self.hf_list[i]].tolist()[T0_date_id+1]
                hf_index = float(self.raw_data.loc[self.raw_data['日期']==date_list[i], self.hf_list[i]])
                hf_nav = hf_nav/hf_index
                date_diff = float((T0_date - date_list[i]).days)
                hf_ra = hf_nav**(365/date_diff) - 1
                hf_return.append(hf_ra)
            # 生成基准（沪深300）自每个成分基金成立以来年化收益率
                bm_nav = self.benchmark_data[self.hf_list[i]].tolist()[T0_date_id+1]
                bm_index = float(self.benchmark_data.loc[self.benchmark_data['日期']==date_list[i], self.hf_list[i]])
                bm_nav = bm_nav/bm_index
                bm_ra = bm_nav**(365/date_diff) - 1
                benchmark_return.append(bm_ra)            
        return hf_return, benchmark_return
    
    def max_drawdown(self, T0_date):
        date_list = self.found_date()
        hf_max_dd = []
        benchmark_max_dd = []
        raw_date = self.raw_data['日期'].tolist()[1:]
        T0_date_id = raw_date.index(T0_date)
        for i in range(len(self.hf_list)):
            if float((T0_date - date_list[i]).days) <= 0:
                drawdown = np.nan
                hf_max_dd.append(drawdown)
                benchmark_max_dd.append(drawdown)
            else:
            # 生成成分基金成立以来最大回撤
                hf_nav = self.raw_data[self.hf_list[i]].tolist()[T0_date_id+1:]
                hf_nav = [x for x in hf_nav if str(x) != 'nan'] # 去除空值
                drawdown_hf_rv = []
                for j in range(len(hf_nav)):
                    if hf_nav[-1-j] >= max(hf_nav[-1-j:]):
                        drawdown = 0
                    else:
                        drawdown = hf_nav[-1-j]/max(hf_nav[-1-j:])-1
                    drawdown_hf_rv.append(drawdown)
                max_hf = min(drawdown_hf_rv)
                hf_max_dd.append(max_hf)
            # 生成基准（沪深300）自每个成分基金成立以来最大回撤
                bm_nav = self.benchmark_data[self.hf_list[i]].tolist()[T0_date_id+1:]
                bm_nav = [x for x in bm_nav if str(x) != 'nan']
                drawdown_bm_rv = []
                for j in range(len(bm_nav)):
                    if bm_nav[-1-j] >= max(bm_nav[-1-j:]):
                        drawdown = 0
                    else:
                        drawdown = bm_nav[-1-j]/max(bm_nav[-1-j:])-1
                    drawdown_bm_rv.append(drawdown)
                max_bm = min(drawdown_bm_rv)
                benchmark_max_dd.append(max_bm)     
        return hf_max_dd, benchmark_max_dd
    
    def scoring_principal(self, hf_value, bm_value, up_interval, down_interval):
        if hf_value <= bm_value:
            if hf_value > (bm_value-down_interval) and hf_value <= bm_value:
                hf_score = 5
            elif hf_value > (bm_value-down_interval*2) and hf_value <= (bm_value-down_interval):
                hf_score = 4
            elif hf_value > (bm_value-down_interval*3) and hf_value <= (bm_value-down_interval*2):
                hf_score = 3
            elif hf_value > (bm_value-down_interval*4) and hf_value <= (bm_value-down_interval*3):
                hf_score = 2
            elif hf_value > (bm_value-down_interval*5) and hf_value <= (bm_value-down_interval*4):
                hf_score = 1
            elif hf_value <= (bm_value-down_interval*5):
                hf_score = 0
        elif hf_value > bm_value:
            if hf_value > (bm_value) and hf_value < (bm_value+up_interval):
                hf_score = 6
            elif hf_value >= (bm_value+up_interval) and hf_value < (bm_value+up_interval*2):
                hf_score = 7
            elif hf_value >= (bm_value+up_interval*2) and hf_value < (bm_value+up_interval*3):
                hf_score = 8
            elif hf_value >= (bm_value+up_interval*3) and hf_value < (bm_value+up_interval*4):
                hf_score = 9
            elif hf_value >= (bm_value+up_interval*4):
                hf_score = 10
        return hf_score
    
    def scoring1_rr(self, hf_ra, bm_ra):
        up_interval, down_interval = 0.03, 0.02
        score1 = self.scoring_principal(hf_ra, bm_ra, up_interval, down_interval)
        return score1
    
    def scoring2_ar(self, hf_ra):
        up_interval, down_interval = 0.03, 0.02
        bm_value = 0.1
        score2 = self.scoring_principal(hf_ra, bm_value, up_interval, down_interval)
        return score2
    
    def scoring3_max_dd(self, hf_max_dd, bm_max_dd):
        up_interval, down_interval = 0.02, 0.02
        if abs(hf_max_dd) == 0:
            score3 = 10
        else:
            score3 = self.scoring_principal(hf_max_dd, bm_max_dd, up_interval, down_interval)
        return score3
    
    def scoring4_ra_max_dd(self, hf_ra, hf_max_dd):
        up_interval, down_interval = 0.3, 0.3
        if abs(hf_max_dd) == 0:
            score4 = 10
        else:
            hf_value, bm_value = hf_ra/abs(hf_max_dd), 1.5
            score4 = self.scoring_principal(hf_value, bm_value, up_interval, down_interval)
        return score4
    
    def hf_weight(self):
        date_list = self.found_date()
        weight_list = []
        for k in range(len(self.T0_set)):
            hf_ra, bm_ra = self.annual_return(self.T0_set[k])
            hf_max_dd, bm_max_dd = self.max_drawdown(self.T0_set[k])
            score1_list, score2_list, score3_list, score4_list = [], [], [], []
            num = 0
            for i in range(len(hf_ra)):
                if float((self.T0_set[k] - date_list[i]).days) <= 0:
                    score1, score2, score3, score4 = 0, 0, 0, 0
                elif float((self.T0_set[k] - date_list[i]).days) < 90:
                    score1, score2 = np.nan, np.nan
                    score3, score4 = 5, 5
                else:
                    score1 = self.scoring1_rr(hf_ra[i], bm_ra[i])
                    score2 = self.scoring2_ar(hf_ra[i])
                    score3 = self.scoring3_max_dd(hf_max_dd[i], bm_max_dd[i])
                    score4 = self.scoring4_ra_max_dd(hf_ra[i], hf_max_dd[i])
                    num += 1
                score1_list.append(score1)
                score2_list.append(score2)
                score3_list.append(score3)
                score4_list.append(score4)
            weight = pd.DataFrame({'T0日期': self.T0_set[k],
                                   '成分基金': self.hf_list,
                                   '分数1': score1_list,
                                   '分数2': score2_list,
                                   '分数3': score3_list,
                                   '分数4': score4_list})
            weight['分数1'].fillna(weight['分数1'].sum()/num, inplace = True)
            weight['分数2'].fillna(weight['分数2'].sum()/num, inplace = True)
            weight['分数'] = weight['分数1'] + weight['分数2'] + weight['分数3'] + weight['分数4']
            weight['权重'] = weight['分数']/weight['分数'].sum()
            weight_list.append(weight)
        weight_output = pd.concat(weight_list, axis = 1)
        
        return weight_output
    
    def output_csv(self):
        weight_output = self.hf_weight()
        weight_output.to_csv('D:/实习&工作/国金自营/私募基金指数/权重数据集/权重.csv', index = False, encoding='utf_8_sig')
        
    def Run(self):
        self.Start_Wind()
        self.output_csv()
        
        
class hf_index_point(): # 每周自动生成指数点位
    
    def __init__(self, hf_inputfile, weight_inputfile, reset_date):
        self.raw_data = pd.read_excel(hf_inputfile)
        self.weight_set = pd.read_csv(weight_inputfile)
        self.hf_list = list(self.raw_data)[1:]
        self.reset_date = reset_date
    
    def main_function(self):
        database_w = self.weight_set
        weight_col = []
        for i in database_w.columns.values.tolist():
            if '权重' in i:
                weight_col.append(i)
        weight_set = []
        for i in weight_col:
            weight = list(database_w[i])
            weight_set.append(weight)
        
        database_nv = self.raw_data.fillna(0, inplace = False)
        net_value_set = database_nv.T.values.tolist()
        for i in range(len(net_value_set)):
            net_value_set[i] = net_value_set[i][1:]
            net_value_set[i].reverse()
        id_T0 = net_value_set[0].index(datetime.strptime(self.reset_date[0],"%Y-%m-%d"))
        for i in range(len(net_value_set)):
            net_value_set[i] = net_value_set[i][id_T0:]
        id_T0_set = []
        for i in self.reset_date:
            id_T0 = net_value_set[0].index(datetime.strptime(i,"%Y-%m-%d"))
            id_T0_set.append(id_T0)
        net_value_change_all = []
        for i in range(len(id_T0_set)):
            net_value_change_set = []
            for j in range(1,len(net_value_set)):
                net_value_change = []
                if net_value_set[j][id_T0_set[i]] == 0:
                    net_value_change = [0 for m in range(id_T0_set[i+1]-id_T0_set[i]+1)]
                    net_value_change_set.append(net_value_change)
                else:
                    if i != len(id_T0_set)-1:
                        for k in range(id_T0_set[i+1]-id_T0_set[i]+1):
                            change_pct = net_value_set[j][id_T0_set[i]+k]/net_value_set[j][id_T0_set[i]] - 1
                            net_value_change.append(change_pct)
                        net_value_change_set.append(net_value_change)
                    else:
                        for k in range(1,(len(net_value_set[0])-id_T0_set[i])):
                            change_pct = net_value_set[j][id_T0_set[i]+k]/net_value_set[j][id_T0_set[i]] - 1
                            net_value_change.append(change_pct)
                        net_value_change_set.append(net_value_change)
            net_value_change_all.append(net_value_change_set)
        
        index_point_T0 = [1000]
        index_point_array = np.array([0])
        for i in range(len(net_value_change_all)):
            nv_change_array = np.array(net_value_change_all[i]).T # m行n列
            weight_array = np.array(weight_set[i]).T # n行1列
            rt_weekly = np.dot(nv_change_array, weight_array)
            index_point = index_point_T0[i]*(1+rt_weekly)
            index_point_T0.append(index_point[-1])
            index_point_array = np.hstack((index_point_array, index_point))
        index_point_array = index_point_array[1:]
        
        return index_point_array
        
        
        
        
'''--------------------------------------------------------------------------------'''
if __name__ == '__main__':
    hf_inputfile = 'D:/实习&工作/国金自营/私募基金指数/数据集/私募成分基金 2.0.xlsx'
    bm_inputfile = 'D:/实习&工作/国金自营/私募基金指数/数据集/私募基金对标指数 2.0.xlsx'
    reset_date = ['2019-12-27','2020-06-24']
    
    # hf_weight = hf_index_weight(hf_inputfile, bm_inputfile, reset_date)
    # hf_weight.Run()
    
    weight_inputfile = 'D:/实习&工作/国金自营/私募基金指数/权重数据集/权重.csv'
    
    hist_point = hf_index_point(hf_inputfile, weight_inputfile, reset_date)
    T_set = hist_point.main_function()
    print(T_set)
    

