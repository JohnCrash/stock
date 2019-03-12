let {companys_task,k_company,dateString,query} = require('./k');
let async = require('async');
/**
 * 计算tech_macd数据
 */
function calc_tech_macd(done){
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
    companys_task('id,kbegin,tech_macd',com=>cb=>{
        k_company(com.id,com.tech_macd?com.tech_macd:com.kbegin,'tech_macd',buildTrader()).then(result=>{
            if(result.endDate){
                console.log(com.id);
                query(`update company set tech_macd='${dateString(result.endDate)}' where id=${com.id}`).then((results)=>cb());
            }else{
                console.log(com.id,'PASSED');
                cb();
            }
        }).catch(error=>{
            cb(error);
        });
    }).then(usetime=>{
        console.log('calc_tech_macd DONE',usetime);
        if(done)done();
    }).catch(err=>{
        console.error('calc_tech_macd',err);
        if(done)done(err);
    });
}

/**
 * 计算年盈利
 */
function calc_macd_year(){

}

/**
 * 计算月盈利
 */
function calc_macd_month(){

}

/**
 * 计算金叉和死叉点
 */
function calc_macd_wave(done){
    query('select * from sta_macd_wave order by date','select date from kd_xueqiu where id=8828 order by date')
    .then((results)=>{
        let waveDates = results[0];
        let kdDates = results[1];
        if(waveDates.length<kdDates.length){
            let startDate = dateString(kdDates[waveDates.length>0?waveDates.length-1:0].date);
            let start = waveDates.length;
            let wave = {};
            for(let i = start;i<kdDates.length;i++)
                wave[dateString(kdDates[i].date)] = [0,0];
            companys_task('id',com=>cb=>{
                query(`select id,date,macd from kd_xueqiu where id=${com.id} and date>='${startDate}'`)
                .then((result)=>{
                    if(result && result.length>0){
                        console.log(com.id,dateString(result[0].date),dateString(result[result.length-1].date));
                        for(let i=1;i<result.length;i++){
                            let K = result[i];
                            let lastK = result[i-1];
                            if( K.macd>0&&lastK.macd<=0){ //buy
                                if(wave[dateString(K.date)])
                                    wave[dateString(K.date)][0]++;
                            }else if(K.macd<0&&lastK.macd>=0){ //sell
                                if(wave[dateString(K.date)])
                                    wave[dateString(K.date)][1]++;
                            }
                        }
                    }else{
                        console.log(com.id,'not found K data');
                    }
                    cb();
                }).catch(err=>cb(err));
            }).then((usetime)=>{
                let task = [];
                for(let i = start;i<kdDates.length;i++){
                    let kd = kdDates[i];
                    let date = dateString(kd.date);
                    task.push(cb=>{
                        query(`insert ignore into sta_macd_wave values ('${date}',${wave[date][0]},${wave[date][1]})`).then(result=>{cb()}).catch(err=>cb(err));
                    });
                }
                async.series(task,(err,result)=>{
                    if(err){
                        console.error(err);
                    }else{
                        if(done)done();
                        console.log('calc_macd_wave DONE',usetime);
                    }
                });
                
            });
        }else{
            console.log('calc_macd_wave DONE');
            if(done)done();
        }
    }).catch((err)=>{
        console.error('calc_macd_wave',err);
        if(done)done(err);
    });
}


/**
 * 计算某天macd从负到正的股票
 */
function calc_macd_select(done){

}
module.exports = {
    calc_tech_macd,
    calc_macd_year,
    calc_macd_month,
    calc_macd_wave,
    calc_macd_select
};
