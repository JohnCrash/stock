/**
 * 使用macd15,30,60...等的行情进行选股
 * 先选出前300只然后在选出行业前五名
 * 将他们分类放入数据库company_select中并且更新xueqiu上关注的股票
 */

const {companys_task,k_company,dateString,query,connection,
    xuequeCookie,xueqiuPostJson,xueqiuGetJson} = require('./k');
const async = require('async');
const macd = require('macd');
const {CompanyScheme,CompanySelectScheme,eqPair,valueList} = require("./dbscheme");


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

/**
 * 计算周期中最大增长
 * N 代表一天有多少个macd数据
 */
function calcMaxGrow(k,macd,N){
    let lastK;
    let lastM;
    let buyK = null;
    let buyI = null;
    let maxK = 0;
    let gain = 1;

    for(let i = 0;i<k.length;i++){
        let v = k[i];
        let m = macd[i];
        if(lastK){
            if(lastM<0 && !buyK && m>0){
                buyK = v;
                buyI = Math.floor(i/N);
            }else if(buyK && buyI != Math.floor(i/N) && m<=0 ){//交易在一天内进行将被排除
                let r;
                if(maxK>0)
                    r = maxK/buyK; //最大值
                else
                    r = v/buyK; //止损

                gain = gain*r;
                buyI = null;
                buyK = null;
                maxK = 0;
            }
        }
        if(buyK && v>maxK && buyI != Math.floor(i/N))maxK = v;
        lastK = v;
        lastM = m;
    }
    if(buyK && buyI != Math.floor((k.length-1)/N) ){ //如果数据最后还没有结算，使用当前价结算
        let r;
        if(maxK>0)
            r = maxK/buyK; //最大值
        else
            r = k[k.length-1]/buyK; //止损

        gain = gain*r;
    }
    return gain;
}

/**
 * 计算周期中最大亏损
 * N 代表一天有多少个macd数据
 */
function calcMaxLoss(k,macd,N){
    let lastK;
    let lastM;
    let buyK = null;
    let buyI = null;
    let gain = 1;

    for(let i = 0;i<k.length;i++){
        let v = k[i];
        let m = macd[i];
        if(lastK){
            if(lastM<0 && !buyK && m < 0){
                buyK = v;
                buyI = Math.floor(i/N);
            }else if(buyK && buyI != Math.floor(i/N) && m > 0 ){//交易在一天内进行将被排除
                let r = v/buyK; 
                gain = gain*r;
                buyI = null;
                buyK = null;
            }
        }
        lastK = v;
        lastM = m;
    }
    if(buyK && buyI != Math.floor((k.length-1)/N) ){ //如果数据最后还没有结算，使用当前价结算
        let r = k[k.length-1]/buyK;
        gain = gain*r;
    }
    return gain;
}

function calcgain_MAX(k,macd,N){
    return [calcMaxGrow(k,macd,N),calcMaxLoss(k,macd,N)];
}

/**
 * 策略1
 */
function strategy1(k,macd,N){
    let gain = 1;
    let maxK = 0;
    let minK = 10000;
    let minI;
    let maxI;
    for(let i = 0;i<k.length;i++){
        let v = k[i];
        let m = macd[i];
        if(m>0){
            if(maxK==0 && minK==10000)continue; //跳过第一个上涨周期
            if(maxK<v){
                maxI = Math.floor((i)/N);
                maxK = v;
            }
        }else{
            if(maxK!=0 && minK!=10000){
               let r = minI==maxI?minK/maxK:maxK/minK; //碰到一天内骗的这里做惩罚性处理
                gain *= r;
                maxK = 0;
                minK = 10000;
            }
            if(minK>v){
                minI =  Math.floor((i)/N);
                minK = v;
            }
        }
    }
    if(maxK!=0 && minK!=10000){
        let r = minI==maxI?minK/maxK:maxK/minK; //碰到一天内骗的这里做惩罚性处理
        gain *= r;
    }
    return gain;
 }

function bookmarkTask(k,bookmark,total,top){
    return (cb)=>{
        query(`SELECT name,code,category,${k} FROM stock.company_select where k15_maxdrawal>0.9 and k15_maxdrawal<1.1 and k15_max*.9 > k15_maxdrawal and static60>=1 and static30>1 order by ${(k)} desc limit ${total}`).then(companys=>{
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

const klv={
    "15":{N:16,limit:16*22}, //一个月
    "60":{N:4,limit:4*44}  //两个月
}
/**
 * 根据不同的k线级别进行标记
 */
function bookmark_by_level(com,lv,cb){
    query(`select * from k${lv}_xueqiu where id=${com.id} order by timestamp desc limit ${klv[lv].limit}`).then(results=>{
        let kclose = [];
        let macd = [];
        
        results.reverse().forEach((k) => {
            kclose.push(k.close);
            macd.push(k.macd);
        });
        let r = calcgain_MAX(kclose,macd,klv[lv].N);
        r.push(kclose[0]);
        if(lv==15){
            r.push(strategy1(kclose,macd,klv[lv].N));
        }
        cb(null,r);
    }).catch(err=>{
        cb(err);
    });
}
/**
 * 计算15,60,kd的macd并进行选股
 */
function research_k15(done){
    companys_task('id',com=>cb=>{
        //更新ma5diff,ma10diff,ma20diff,ma30diff,当前股价和均线的差值
        query(`select close,ma5,ma10,ma20,ma30 from kd_xueqiu where id=${com.id} order by date desc limit 1`).then(R=>{
            if(R.length===1){
                let price = R[0].close;//更新当前股价price
                let ma5diff = price-R[0].ma5;
                let ma10diff = price-R[0].ma10;
                let ma20diff = price-R[0].ma20;
                let ma30diff = price-R[0].ma30;
                
                async.series([callback=>bookmark_by_level(com,15,callback),
                        callback=>bookmark_by_level(com,60,callback)],
                    (err,results)=>{
                    if(err){
                        console.error(err);
                        cb();
                    }
                    let [k15_max,k15_maxdrawal,b15,strategy1] = results[0];
                    let [k60_max,k60_maxdrawal,b60] = results[1];
                    //更新静态收益static30,static60
                    let static30,static60;
                    static30 = b15?price/b15:1;
                    static60 = b60?price/b60:1;
                    console.log(com.id,price,static30,static60);
                    let db = {price,static30,static60,ma5diff,ma10diff,ma20diff,ma30diff,k15_max,k15_maxdrawal,k60_max,k60_maxdrawal,strategy1};
                    query(`update company_select set ${eqPair(db,CompanySelectScheme)} where company_id=${com.id}`).then(results=>{
                        cb();
                    }).catch(err=>{
                        console.error(err);
                        cb();
                    });
                });
            }else{
                console.error(com.id);
                cb();
            }
        });
    }).then(usetime=>{
        /**
         * 着这里计算bookmark
         * 使用每个级别分类里面的的前5名将被标记出来
         */
        /*
        let task = [];
        task.push(bookmarkTask('k15_max','bookmark15',200,2));
        task.push(bookmarkTask('k60_max','bookmark60',200,2));

        async.series(task,(err,results)=>{
            console.log('research_k15 DONE!');

            if(done)done();
        });
        */
       //不做bookmark,简单的看谁强,见(research_hot.js)
       console.log('research_k15 DONE!');

       if(done)done();
    });   
}

module.exports = {research_k15};