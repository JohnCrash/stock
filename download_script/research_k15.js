const {companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');
const macd = require('macd');
const {CompanyScheme,CompanySelectScheme,eqPair,valueList} = require("./dbscheme");
const {update_company} = require('./desc');
const Crawler = require("crawler");

function arrayScale(a,n){
    let s = [];
    for(let it of a){
        for(let i=0;i<n;i++)
            s.push(it);
    }
    return s;
}  
 
function tailArray(d,r){
    if(d && r){
        let a = [];
        for(let i=Math.floor(d.length*(1-r));i<d.length;i++){
            a.push(d[i]);
        }
        return a;
    }else return d;
}

function calcgain(k0,macd0,r){
    let lastK;
    let lastM;
    let buyK;
    let gain = 1;
    let maxdrawal = 0;
    let acc = 0;
    let k = tailArray(k0,r);
    let macd = tailArray(macd0,r);
    for(let i = 0;i<k.length;i++){
        let v = k[i];
        let m = macd[i];
        if(lastK){
            if(lastM<0 && m>0){
                buyK = v; 
            }else if(buyK && m<0){
                //trade(buyK,v);
                let r = v/buyK;
                gain = gain*r;

                if(r<1){
                    acc += (1-r);
                }else{
                    if(acc>maxdrawal)maxdrawal = acc;
                    acc = 0;
                }

                buyK = undefined;
            }  
        }
        lastK = v;
        lastM = m;
    }
    if(acc>maxdrawal)maxdrawal = acc;
    return [gain,maxdrawal>0?(gain-1)/maxdrawal:(gain-1)/0.1];
}

function calcgain_MAX(k0,macd0,r){
    let lastK;
    let lastM;
    let buyK;
    let maxK = 0;
    let gain = 1;
    let maxdrawal = 0;
    let acc = 0;
    let k = tailArray(k0,r);
    let macd = tailArray(macd0,r);    
    for(let i = 0;i<k.length;i++){
        let v = k[i];
        let m = macd[i];
        if(lastK){
            if(lastM<0 && m>0){
                buyK = v;
            }else if(buyK && m<0){
                //trade(buyK,v);
                let r = maxK/buyK;

                gain = gain*r;

                if(r<1){
                    acc += (1-r);
                }else{
                    if(acc>maxdrawal)maxdrawal = acc;
                    acc = 0;
                }

                buyK = undefined;
                maxK = 0;
            }
            if(buyK && v>maxK)maxK = v;
        }
        lastK = v;
        lastM = m;
    }
    if(acc>maxdrawal)maxdrawal = acc;
    return [gain,maxdrawal>0?(gain-1)/maxdrawal:(gain-1)/0.1];
}

function bookmarkTask(k,bookmark,total,top){
    return (cb)=>{
        query(`SELECT name,code,category,${k} FROM stock.company_select order by ${k} desc limit ${total}`).then(companys=>{
            let category = {};
            for(let com of companys){
                let c = com.category?com.category:'未分类';
                category[c] = category[c]?category[c]:[];
                if(category[c].length<=top)
                    category[c].push(com);
            }
            query(`update company_select set ${bookmark}=0`).then(()=>{
                let task = [];
                for(let key in category){
                    let cats = category[key];
                    console.log(key);
                    for(let com of cats){
                        console.log('   ',com.name,com[k]);
                        task.push((callback)=>{
                            query(`update company_select set ${bookmark}=1 where code='${com.code}'`).then(r=>{
                                callback();
                            }).catch(e=>{
                                console.error(e);
                                callback(e);
                            });
                        });
                    }
                }
                async.series(task,(err,results)=>{
                    if(err)console.error(err);
                    cb();
                });
            });
            
        }).catch(err=>{
            console.error(err);
            cb(err);
        });    
    };
}

/**
 * 使用bookmark15更新雪球上的股票
 */
function update_xueqiu(){
    //首先下载雪球的股票列表，然后删除不在榜的。加入上榜的。然后重新分类
    
}

function research_k15(done){
    query(`delete from research_k15`).then(result=>{
        companys_task('id',com=>cb=>{
            query(`select * from k15_xueqiu where id=${com.id} order by timestamp desc limit 800`).then(results=>{
                let k15close = [];
                let k30close = [];
                let k60close = [];
                let k120close = [];
                let kdclose = [];
                let length = results.length;
                
                results.reverse().forEach((k,i) => {
                    k15close.push(k.close);
                    if(i%2==0)k30close.push(k.close);
                    if(i%4==0)k60close.push(k.close);
                    if(i%8==0)k120close.push(k.close);
                    if(i%16==0)kdclose.push(k.close);            
                });
                let macd15 = macd(k15close).histogram;
                let macd30 = macd(k30close).histogram;
                let macd60 = macd(k60close).histogram;
                let macd120 = macd(k120close).histogram;
                let macdday = macd(kdclose).histogram;
                //减少数据量根据反应最近的变化
                let [k15_gain,k15_drawal] = calcgain(k15close,macd15);
                let [k30_gain,k30_drawal] = calcgain(k30close,macd30);
                let [k60_gain,k60_drawal] = calcgain(k60close,macd60);
                let [k120_gain,k120_drawal] = calcgain(k120close,macd120);
                let [kd_gain,kd_drawal] = calcgain(kdclose,macdday);
                let [k15_max,k15_maxdrawal] = calcgain_MAX(k15close,macd15);
                let [k30_max,k30_maxdrawal] = calcgain_MAX(k30close,macd30);
                let [k60_max,k60_maxdrawal] = calcgain_MAX(k60close,macd60);
                let [k120_max,k120_maxdrawal] = calcgain_MAX(k120close,macd120);    
                let [kd_max,kd_maxdrawal] = calcgain_MAX(kdclose,macdday);


                //更新ma5diff,ma10diff,ma20diff,ma30diff,当前股价和均线的差值
                query(`select close,ma5,ma10,ma20,ma30 from kd_xueqiu where id=${com.id} order by date desc limit 1`).then(R=>{
                    if(R.length===1){
                        let price = R[0].close;//更新当前股价price
                        let ma5diff = price-R[0].ma5;
                        let ma10diff = price-R[0].ma10;
                        let ma20diff = price-R[0].ma20;
                        let ma30diff = price-R[0].ma30;
                        //更新静态收益static30,static60
                        let static30,static60;
                        let b30 = k15close.length>16*22?k15close.length-16*22:k15close.length;
                        let b60 = k15close.length>16*44?k15close.length-16*44:k15close.length;
                        static30 = price/k15close[k15close.length-b30];
                        static60 = price/k15close[k15close.length-b60];               
                        console.log(com.id,price,static30,static60)
                        let db = {price,static30,static60,ma5diff,ma10diff,ma20diff,ma30diff,k15_gain,k15_drawal,k30_gain,k30_drawal,k60_gain,k60_drawal,k120_gain,k120_drawal,kd_gain,kd_drawal,
                            k15_max,k15_maxdrawal,k30_max,k30_maxdrawal,k60_max,k60_maxdrawal,k120_max,k120_maxdrawal,kd_max,kd_maxdrawal};
                        query(`update company_select set ${eqPair(db,CompanySelectScheme)} where company_id=${com.id}`).then(results=>{
                            cb();
                        });
                    }else{
                        console.error(com.id);
                        cb();
                    }
                });
            }).catch(err=>{
                cb(err);
            });
        }).then(usetime=>{
            /**
             * 着这里计算bookmark
             * 使用每个级别分类里面的的前5名将被标记出来
             */
            let task = [];
            task.push(bookmarkTask('k15_max','bookmark15',300,5));
            task.push(bookmarkTask('k30_max','bookmark30',300,5));
            task.push(bookmarkTask('k60_max','bookmark60',300,5));
            task.push(bookmarkTask('k120_max','bookmark120',300,5));
            task.push(bookmarkTask('kd_max','bookmarkd',300,5));
            async.series(task,(err,results)=>{
                console.log('DONE!');
                if(done)done();
            });
        });
    }).catch(err=>{
        console.error(err);
        if(done)done(err);
    });    
}

module.exports = {research_k15};