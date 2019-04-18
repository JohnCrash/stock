/**
 * 对精选出来的热点股票进行跟踪
 */
const {companys_task,k_company,dateString,query,connection,
    xuequeCookie,xueqiuPostJson,xueqiuGetJson} = require('./k');
const async = require('async');
const macd = require('macd');
/**
 * 只要是星期一直五，交易时间没15分钟做一次计算
 */
function watchMainLoop(){
    /** stocks
     *  [   {
                "symbol": "SH603538",
                "name": "美诺华",
                "type": 11,
                "remark": "",
                "exchange": "SH",
                "created": 1555574210993,
                "group":[...] //增加的股票所在的组，updateGroup中处理增加的字段
                "k15":true|false //中间数据表示15分钟级别的macd是否翻红
                "k30":true|false
                "k60":true|false
            },...
        ]
     */
    let stocks;
    /** category
     * [   {
                "id": 22, //pid
                "name": "K15",
                "order_id": 1,
                "category": 1,
                "include": false,
                "type": 1,
                "created_at": 1555576031795,
                "updated_at": 1555576031795,
                "stocks":[] 分类中包含的股票列表，updateGroup中处理增加的字段
            },...
        ]
     */
    let category;
    let lastDay; //最近一次成功调用updateStocks时是星期几
    let lastMinutes;//最近一次成功调用watchHot时几分钟前

    function is9H(t){
        let day = t.getDay();
        if(day>=1 && day<=5 && t.getHours()==9 && lastDay!=day){
            return true;
        }
        return false;
    }
    function is15M(t){
        let minutes = t.getMinutes();
        if(lastMinutes!=minutes && minutes%15==0){
            return true;
        }
        return false;
    }
    function updateGroup(cb){
        if(category && stocks){
            let task = [];
            //先初始化stocks中的group
            let mapSymbol2Stock = {};
            for(let stock of stocks){
                stock.group = [];
                mapSymbol2Stock[stock.symbol] = stock;
            }
            //先初始化category中的stocks
            for(let cat of category){
                cat.stocks = [];
            }
            for(let it of category){
                if(it.id>0) //自定义的股票分类
                    task.push((callback)=>{
                        xueqiuGetJson(`https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=${it.id}&category=1`,
                        (err,json)=>{
                            if(json){
                                if(json.data && json.data.stocks && json.data.stocks.length>0){
                                    for(let s of json.data.stocks){
                                        it.stocks.push(mapSymbol2Stock[s.symbol]);
                                        if(s.include){//对应的股票在该分类中
                                            mapSymbol2Stock[s.symbol].group.push(it.name);
                                        }
                                    }
                                }
                            }
                            callback();
                        });
                    });
            }
            async.parallelLimit(task,5,(err,results)=>{
                if(err)console.error(err);
                cb();
            });
        }else cb();
    }
    function updateStocks(cb){
        let tasks = [];
        tasks.push((callback)=>{
            xueqiuGetJson('https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1',
            (err,json)=>{
                if(json){
                    console.log('WATCH',json.data.stocks.length);
                    if(json.data && json.data.stocks && json.data.stocks.length>0)
                        stocks = json.data.stocks; 
                }
                callback();
            });
        });
        tasks.push((callback)=>{
            xueqiuGetJson('https://stock.xueqiu.com/v5/stock/portfolio/list.json',
            (err,json)=>{
                if(json){
                    if(json.data && json.data.stocks && json.data.stocks.length>0)
                        category = json.data.stocks; 
                }
                callback();
            });
        });
        async.parallel(tasks,(err,results)=>{
            if(err){
                console.log(err);
                stocks = null;
                category = null;
            }
            //stocks中的每只股票的分类放入group中
            updateGroup(cb);
        });
    }
    setInterval(()=>{
        let t = new Date();
        if(!stocks || is9H(t)){ //如果stocks不存在或者每天早晨9点准时更新监视列表
            udpdateStocks(()=>{
                if(stocks){
                    lastDay = t.getDay();
                    watchHot(stocks,category);
                }
            });
        }

        if(stocks && is15M(t)){ //每15分钟就做一次监视处理
            lastMinutes = t.getMinutes();
            watchHot(stocks,category,15);
        }                
    },1000);
}  

function getPID(category,n){
    for(let it of category){
        if(it.name === `K${n}`){
            return it.id;
        }
    }
    return 0;
}

//将股票加入雪球'全部'分类中
//https://xueqiu.com/v4/stock/portfolio/addstock.json
//POST category:2 symbol:code
function addStock(code){
    return (cb)=>{
        xueqiuPostJson('https://xueqiu.com/v4/stock/portfolio/addstock.json',
            {symbol:code,category:2},
            (err)=>{
                cb(err);
        });
    };
}

//将股票从雪球'全部'分类中删除
//https://stock.xueqiu.com/v5/stock/portfolio/stock/cancel.json
//POST symbol:code
function deleteStock(code){
    return (cb)=>{
        xueqiuPostJson('https://stock.xueqiu.com/v5/stock/portfolio/stock/cancel.json',
            {symbols:code},
            (err)=>{
                cb(err);
        });
    };
}

//对股票进行分组
function groupStock(group,name,code){
    return (cb)=>{
        xueqiuPostJson('https://stock.xueqiu.com/v5/stock/portfolio/stock/modify_portfolio.json',
            {pnames:group.join(','),symbols:code,category:1},
            (err)=>{
                console.log('GROUP',name,code,group.join('|'));
                cb(err);
        });
    };
}

/**
 * 判断为金叉返回true
 * data = {
 * 
 * }
 */
function isGoldCross(data,n){

}
/**
 * 开始下载每只股票的k线数据，然后最近的macd关系
 */
function watchStocks(stocks,n,cb){
    let task = [];
    let timestamp = Date.now();

    for(let s of stocks){
        task.push((cb)=>{
            xueqiuGetJson(`https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${s.symbol}&begin=${timestamp}&period=${n}m&type=before&count=-8&indicator=kline`,
            (err,json)=>{
                if(!err && json){
                    if(isGoldCross(json.data,n)){
                        s[`k${n}`] = true;
                    }else{
                        s[`k${n}`] = false;
                    }
                }
                cb();
            });
        });
    }
    async.parallelLimit(task,5,(err,results)=>{
        if(err)console.error(err);
        cb();
    });
}
/**
 * 使用15分钟k线图监视stocks列表中的股票，如果macd由负即将转正，或者转正4个点内，该股票将被放入到K15中去
 * 首先找到需要加入的，然后删除不需要加入的
 */
function watchHot(stocks,category,n){
    xueqiuGetJson(`https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=${getPID(category,n)}&category=1`,
        (err,json)=>{
            if(json){
                let kc; //分类中现存的股票列表
                if(json.data && json.data.stocks && json.data.stocks.length>0){
                    kc = json.data.stocks;
                    watchStocks(stocks,n,(sc)=>{ //sc是即将变正的列表
                    
                    });
                }
            }
        });
}

watchMainLoop();

module.exports = {watchMainLoop};
