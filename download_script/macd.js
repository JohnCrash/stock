let {companys_task,k_company,dateString} = require('./k');

/**
 * 计算tech_macd数据
 */
function calc_tech_macd(){
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
                    console.log(buyK.close,maxK.close);
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
    companys_task('id,kbegin,tech_macd',(com,connection)=>cb=>{
        k_company(com.id,com.tech_macd?com.tech_macd:com.kbegin,'tech_macd',buildTrader()).then(result=>{
            console.log(com.id);
            if(result.endDate){
                connection.query(`update company set tech_macd='${dateString(result.endDate)}' where id=${com.id}`,(err,results)=>{
                    if(err){
                        cb(err);
                    }else{
                        cb();
                    }
                });    
            }else{
                console.log(com.id,'PASSED');
                cb();
            }
        }).catch(error=>{
            cb(error);
        });
    }).then(usetime=>{
        console.log('calc_tech_macd DONE',usetime);
    }).catch(err=>{
        console.error(err);
    });
}

/**
 * 计算年盈利
 */
function calc_macd_year(){

}

/**
 * 计算买入卖出波次
 */
function calc_macd_wave(){

}

/**
 * 计算某天macd从负到正的股票
 */

module.exports = {calc_tech_macd,calc_macd_year,calc_macd_wave};
