let {companys_task,k_company,dateString,query} = require('./k');
let async = require('async');
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
            k_company(com.id,com.tech_macd?com.tech_macd:com.kbegin,'tech_macd',buildTrader()).then(result=>{
                if(result.lastSellDate){
                    console.log('tech_macd',com.id,dateString(result.lastSellDate));
                    query(`update company set tech_macd='${dateString(result.lastSellDate)}' where id=${com.id}`).then((results)=>cb());
                }else{
                    console.log('tech_macd',com.id,'PASSED');
                    cb();
                }
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
 * 当计算calc_macd_select后可以简单的算出金叉和是死叉数量
 * 金叉数量
 * SELECT count(*) FROM stock.select_macd where date='2019-3-13' and state=1
 * 死叉数量
 * SELECT count(*) FROM stock.select_macd where date='2019-3-13' and state=2
 */
function calc_macd_wave(done){
    //8828 是SH000001指数
    query('select * from sta_macd_wave order by date','select date from kd_xueqiu where id=8828 order by date')
    .then((results)=>{
        let waveDates = results[0];
        let kdDates = results[1];
        if(waveDates.length<kdDates.length){
            let startDate = dateString(kdDates[waveDates.length>0?waveDates.length-1:0].date);
            let start = waveDates.length;
            let wave = {};
            for(let i = start;i<kdDates.length;i++)
                wave[dateString(kdDates[i].date)] = [0,0,0,0];
            companys_task('id',com=>cb=>{
                query(`select id,date,macd from kd_xueqiu where id=${com.id} and date>='${startDate}'`)
                .then((result)=>{
                    if(result && result.length>0){
                        console.log('calc_macd_wave',com.id,dateString(result[0].date),dateString(result[result.length-1].date));
                        for(let i=1;i<result.length;i++){
                            let K = result[i];
                            let lastK = result[i-1];
                            let dateStr = dateString(K.date);
                            if( K.macd>0&&lastK.macd<=0){ //buy
                                if(wave[dateStr])
                                    wave[dateStr][0]++;
                            }else if(K.macd<0&&lastK.macd>=0){ //sell
                                if(wave[dateStr])
                                    wave[dateStr][1]++;
                            }
                            if(K.macd>=0){
                                if(wave[dateStr])
                                    wave[dateStr][2]++;
                            }else{
                                if(wave[dateStr])
                                    wave[dateStr][3]++;
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
                        query(`insert ignore into sta_macd_wave values ('${date}',${wave[date][0]},${wave[date][1]},${wave[date][2]},${wave[date][3]})`).then(result=>{cb()}).catch(err=>cb(err));
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
 * 将select_macd和select_macd_ready中的状态更新到company_detail中去
 */
function update_company_daital_select(cb){
    const days = ['today','yesterday','threeday'];
    query('update company_detail set ready=0,today=0,yesterday=0,threeday=0','select distinct(date) from select_macd order by date desc limit 3')
    .then(results=>{
        let result = results[1];
        let task = [];
        let dd = result[0].date;
        for(let i=0;i<result.length;i++){
            let d = result[i].date;
            task.push(cb=>{
                query(`select * from select_macd where date='${dateString(d)}'`)
                .then(result=>{
                    let t = [];
                    for(let s of result){
                        t.push(cb=>{
                            console.log('update',days[i],s.id);
                            query(`update company_detail set ${days[i]}=${s.state} where company_id=${s.id}`).then(r=>cb()).catch(err=>cb(err));
                        });
                    }
                    async.series(t,(err,r)=>{
                        cb(err);
                    });
                }).catch(err=>{
                    console.error(err);
                    cb(err);
                });
            });
        }
        task.push(cb=>{
            query(`select * from select_macd_ready where date='${dateString(dd)}'`)
            .then(result=>{
                let t = [];
                for(let s of result){
                    t.push(cb=>{
                        console.log('ready',s.id);
                        query(`update company_detail set ready=${s.ready} where company_id=${s.id}`).then(r=>cb()).catch(err=>cb(err));
                    });
                }
                async.series(t,(err,r)=>{
                    cb(err);
                });
            }).catch(err=>{
                console.error(err);
                cb(err);
            });
        });
        async.series(task,(err,result)=>{
            cb(err);
        });
    }).catch(err=>{
        console.error(err);
        cb(err);
    });
}

/**
 * 计算某天macd从负到正的股票
 */
function calc_macd_select(done){
    query('select date from kd_xueqiu where id=8828 order by date','select distinct(date) from select_macd order by date desc')
    .then(([kd,ss])=>{
        let startDate;
        if(ss.length>0){
            for(let i=kd.length-1;i>0;i--){
                let kdate = dateString(kd[i].date);
                let sdate = dateString(ss[0].date);
                if(kdate === sdate){
                    if(i===kd.length-1){
                        //已经做过了
                        console.log('calc_macd_select PASSED');
                        if(done)done();
                        return;
                    }
                    startDate = dateString(kd[i-1].date);
                    break;
                }
            }
            if(!startDate){
                console.error('calc_macd_select startDate=null');
                if(done)done(1);
            }
        }else{
            startDate = dateString(kd[kd.length-2].date);
        }
        let macdvol = {};
        companys_task('id',com=>cb=>{
            query(`select id,date,macd from kd_xueqiu where id=${com.id} and date>='${startDate}'`)
            .then((result)=>{
                if(result && result.length>0){
                    console.log('calc_macd_select',com.id,dateString(result[0].date));
                    for(let i=1;i<result.length;i++){
                        let K = result[i];
                        let lastK = result[i-1];
                        let dateStr = dateString(K.date);
                        if(!macdvol[date]){
                            macdvol[date] = [0,0];
                        }
                        if(K.macd>=0){
                            macdvol[date][0]++;
                        }else{
                            macdvol[date][1]++;
                        }
                        if( K.macd>0&&lastK.macd<=0){ //buy
                            query(`insert ignore into select_macd values (${com.id},'${dateStr}',1)`);
                        }else if(K.macd<0&&lastK.macd>=0){ //sell
                            query(`insert ignore into select_macd values (${com.id},'${dateStr}',2)`);
                        }else if(K.macd<0&&2*K.macd-lastK.macd>0){ //buy
                            query(`insert ignore into select_macd_ready values (${com.id},'${dateStr}',1)`);
                        }else if(K.macd>0&&2*K.macd-lastK.macd<0){ //sell
                            query(`insert ignore into select_macd_ready values (${com.id},'${dateStr}',2)`);
                        }
                    }  
                }else{
                    console.log(com.id,'not found K data');
                }
                cb();
            })
        }).then(usetime=>{
            /**
             * 将select_macd和select_macd_ready中的数据更新到company_daital中，这样缓存以后查询更加快捷
             */
            update_company_daital_select(cb=>{
                console.log('calc_macd_select DONE',usetime);
                if(done)done(null,macdvol);
            });
        }).catch(err=>{
            if(done)done(err);
        });
    }).catch(err=>{
        console.error('calc_macd_select',err);
        if(done)done(err);
    });
}

/**
 * 如果连续计算tech_macd,macd_wave,macd_select
 */
function macd(done){
    calc_macd_select((err,macdvol)=>{
        if(err){
            if(done)done(err);
            return;
        }
        //计算macd_wave
        query('select * from sta_macd_wave order by date desc limit 1','select distinct(date) from select_macd order by date desc')
        .then(([sta_macd_wave_date,select_macd_date])=>{
            let dd = sta_macd_wave_date[0].date //sta_macd_wave统计最后的日期
            let dds = [];
            for(let i=0;i<select_macd_date.length;i++){
                if(select_macd_date[i].date>dd)
                    dds.push(select_macd_date[i].date);
            }
            //需要更新的日期都在dds中了
            let tasks = [];
            let ids = {}; //需要重新计算tech_macd的公司id列表
            for(let d of dds){
                tasks.push(cb=>{
                    /*
                    * 金叉数量
                    * SELECT count(*) FROM stock.select_macd where date='2019-3-13' and state=1
                    * 死叉数量
                    * SELECT count(*) FROM stock.select_macd where date='2019-3-13' and state=2
                    */
                   let ds = dateString(d);
                   query(`select * from select_macd where date='${ds}'`)
                   .then(result=>{
                       let buys = 0;
                       let sells = 0;
                       for(let it of result){
                           if(it.state===1)
                                buys++;
                            else if(it.state===2)
                                sells++;
                           ids[it.id]=true;
                       }
                       if(macdvol[ds] && macdvol[ds].length===2){
                        query(`insert ignore into sta_macd_wave values ('${ds}',${buys},${sells},${macdvol[ds][0]},${macdvol[ds][1]})`);
                        cb();
                       }
                        else{
                            let err = `macdvol ${ds} ${macdvol}`;
                            console.error(err);
                            cb(err);
                        }
                   }).catch(err=>{
                        if(done)done(err);
                        cb(err);
                   });
                });
            }
            async.series(tasks,err=>{
                if(err){
                    if(done)done(err);
                }else{
                    if(!ids){
                        if(done)done();
                    }else
                        calc_tech_macd(done,ids);
                }
            })
        }).catch(err=>{
            if(done)done(err);
        });
        //计算tech_macd
    })
}

module.exports = {
    calc_tech_macd,
    calc_macd_year,
    calc_macd_month,
    calc_macd_wave,
    calc_macd_select,
    update_company_daital_select,
    macd
};
