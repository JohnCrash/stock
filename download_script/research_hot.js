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
    function isTranTime(t){
        let day = t.getDay();
        let hours = t.getHours();

        return day>=1 && day<=5 && hours>=9 && hours<=15 && hours!=12;
    } 
    function is15M(t){
        let minutes = t.getMinutes();
        if( isTranTime(t) && lastMinutes!=minutes && minutes%15==0){ //这里加入判断实在交易时间进行的操作
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
                                        mapSymbol2Stock[s.symbol].group.push(it.name);
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
    let isUpdateStocks = false; //防止多次同时进入updateStocks
    setInterval(()=>{
        let t = new Date();
        if(!isUpdateStocks && (!stocks || is9H(t))){ //如果stocks不存在或者每天早晨9点准时更新监视列表
            isUpdateStocks = true;
            updateStocks(()=>{
                if(stocks){
                    lastDay = t.getDay();
                    watchHot(stocks,category,15);
                }
                isUpdateStocks = false;
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

//参见xueqiu_k15.js
let columns = [
    "timestamp",
    "volume",
    "open",
    "high",
    "low",
    "close",
    "chg",
    "percent",
    "turnoverrate",
    "amount",
    "dea",
    "dif",
    "macd"];
let column2index = {};
for(let k in columns){
    column2index[columns[k]] = k;
}
let macdidx = column2index['macd'];
function checkColumns(c0,c1){
    if(c0.length===c1.length){
        for(let i=0;i<c0.length;i++){
            if(c0[i]!==c1[i])return false;
        }
        return true;
    }
    return false;
}

function getMACD(data){
    if(data && data.column && data.item && data.item.length>=8 && checkColumns(columns,data.column)){
        return data.item.map((it)=>{
            return it[macdidx];
        }).reverse();
    }
    return [];
}
/**
 * 判断为金叉返回true
 * data = {
 *      column:["timestamp","volume"...],
 *      item:[] //0是最近的
 * }
 */
function isGoldCross(m,n){
    if(m.length>=8){
        let len = m.length;
        //1头是红的尾巴绿两个点，直接确认
        if(m[0]>=0 && m[len-1] < 0 && m[len-2] < 0){
            return true;
        }
        //2如果全部是绿的，并且结尾向上有收红红迹象
        for(let i=0;i<len;i++){
            if(m[i]>=0){
                return false;
            }
        }
        if( 2*(m[0]-m[1]) >= -m[0] ){ //略微提前一点
            return true;
        }
    }
    return false;
}
/**
 * 开始下载每只股票的k线数据，然后最近的macd关系
 */
function watchStocks(stocks,n,cb){
    let task = [];
    let timestamp = Date.now();

    for(let s of stocks){
        task.push((cb)=>{
            xueqiuGetJson(`https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${s.symbol}&begin=${timestamp}&period=${n}m&type=before&count=-8&indicator=kline,macd,dif,dea`,
            (err,json)=>{
                if(!err && json){
                    if(isGoldCross(getMACD(json.data),n)){
                        s[`k${n}`] = true;
                        console.log(s.name,'GOLD',`K${n}`);
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
function mapTable(t,k){
    let m = {};
    for(let it of t){
        m[it[k]] = it;
    }
    return m;
}
function removeGroup(group,name){
    let i = group.indexOf(name);
    if(i>0){
        group.splice(i,1);
    }
}
function insertGroup(group,name){
    if(group.indexOf(name)==-1){
        group.push(name);
    }
}
function getCategoryByName(cats,name){
    for(let it of cats){
        if(it.name==name)
            return it;
    }
    return null;
}
/**
 * 使用15分钟k线图监视stocks列表中的股票，如果macd由负即将转正，或者转正4个点内，该股票将被放入到K15中去
 * 首先找到需要加入的，然后删除不需要加入的
 */
function watchHot(stocks,category,n){
    let cats = getCategoryByName(category,`K${n}`);
    if(cats){
        watchStocks(stocks,n,()=>{ 
            let sc = []; //sc是即将变正的列表
            for(let it of stocks){
                if(it[`k${n}`]){
                    sc.push(it);
                }
            }
            let kc =  cats.stocks;//分类中现存的股票列表
            let symbol2sc = mapTable(sc,'symbol');
            let symbol2kc = mapTable(kc,'symbol');
    
            let i = kc.length;
            while(i--){
                let s = kc[i];
                if(!symbol2sc[s.symbol]){//如果不在sc表中,删除
                    kc.splice(i,1);//分类中的删除
                    removeGroup(s.group,`K${n}`); //这只股票将不在该组中了
                    groupStock(s.group,s.name,s.symbol)(()=>{}); //调整分组
                }
            }
            for(let s of sc){
                //如果不在kc表中,加入
                if(!symbol2kc[s.symbol]){
                    kc.push(s);//分类中添加
                    insertGroup(s.group,`K${n}`);
                    groupStock(s.group,s.name,s.symbol)(()=>{}); //调整分组
                }
            }
        });
    }else{
        console.error(`Can't found category K${n}`);
    }
}

watchMainLoop();

module.exports = {watchMainLoop};
