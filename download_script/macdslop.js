let {companys_task,dateString,query,connection} = require('./k');
let async = require('async');

  /**
   * 遍历公司的k数据
   * id公司id,kstart起始日期
   * trader_callback 交易者回调
   *    每个k数据都会给trader_callback,并且给交易函数sell
   * 使用举例
   *  k_company(134,'2019-3-8','tech_macd',(k,sell)=>{
   *    ...
   *  }).then(results=>{
   *    ...
   *  });
   */
  function k_company(id,kstart,db,trader_callback){
    return new Promise((resolve,reject)=>{
        let t0 = Date.now();
        let lastSellDate;
        function sell(buy,sell,max){
            if(buy && sell){
                let buy_value = buy.close;
                let sell_value = sell.close;
                let max_value = max.close;
                let dd = Math.floor((sell.date-buy.date)/(3600*24*1000));
                let max_dd = Math.floor((max.date-buy.date)/(3600*24*1000));
                //每年股市开盘时间为243天
                let rate = ((sell_value-buy_value))/(buy_value);
                let max_rate = ((max_value-buy_value))/(buy_value);
                lastSellDate = sell.date;
                let sqlstr = `insert ignore into ${db} values (${id},'${dateString(buy.date)}','${dateString(sell.date)}',${buy_value},${sell_value},${rate},${dd},'${dateString(max.date)}',${max_rate},${max_dd},${max_value},${buy.dif},${buy.dea})`;
    
                connection.query(sqlstr,(error, results, field)=>{
                    if(error)console.error(id,error);
                });
            }
        }
        let startDate = dateString(new Date(kstart));
        connection.query(`select date,open,close,macd,dif,dea from kd_xueqiu where id=${id} and date>='${startDate}'`,(error, results, field)=>{
            if(error){
                console.error(id,error);
                reject(error);
            }else{
                for(let it of results){
                    trader_callback(it,sell);
                }
                if(results.length>0){
                    resolve({
                        beginDate:results[0].date,
                        endDate:results[results.length-1].date,
                        lastSellDate,
                        usetime:Date.now()-t0
                    });
                }else{
                    resolve({usetime:Date.now()-t0});
                }
            }   
        });
    });
}

/**
 * 计算tech_macd数据
 * 从上次k死叉点向后搜索kd_xueqiu
 * 因此其实如果发生死叉计算重新计算是浪费时间，使用calc_macd_wave的提示来计算更加合理
 * 如果提供ids就只更新ids中存在的公司
 */
function calc_tech_macd(done,ids){
    function buildTrader(){
        let lastK;
        let maxK;
        let buyK;
        return (k,trade)=>{
            if(lastK){
                if(lastK.macd<0 && k.macd>0){
                    buyK = k;
                }else if(buyK && k.macd<0){
                    trade(buyK,k,maxK);
                    buyK = undefined;
                    maxK = undefined;
                }
                if(buyK){
                    if(!maxK){
                        maxK = buyK;
                    }else if(k.close>maxK.close){
                        maxK = k;
                    }
                }
            }
            lastK = k
        };
    }
    companys_task('id,kbegin,tech_macd',com=>cb=>{
        if(ids && ids[com.id]){
            cb(); //不需要更新
        }else{
            k_company(com.id,com.kbegin,'tech_macd2',buildTrader()).then(result=>{
                if(result.lastSellDate){
                    console.log('tech_macd2',com.id,dateString(result.lastSellDate));
                }else{
                    console.log('tech_macd2',com.id,'PASSED');
                }
                cb();
            }).catch(error=>{
                cb(error);
            });
        }
    }).then(usetime=>{
        console.log('calc_tech_macd DONE',usetime);
        if(done)done();
    }).catch(err=>{
        console.error('calc_tech_macd',err);
        if(done)done(err);
    });
}

calc_tech_macd(err=>{
    console.log('DONE!')
});