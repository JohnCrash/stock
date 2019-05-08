/**
 * 对精选出来的热点股票进行跟踪
 */
const {companys_task,k_company,dateString,query,connection,
    xuequeCookie,xueqiuPostJson,xueqiuGetJson} = require('./k');
const async = require('async');
const macd = require('macd');

/**
 * 使用bookmark15更新雪球上的股票
 */
function update_xueqiu_list(lv,done){
    //首先下载雪球的股票列表，然后删除不在榜的。加入上榜的。然后重新分类
    let task = [];

    task.push((cb)=>{
        query(`SELECT id,name,simple FROM stock.category`)
        .then(results=>{
            cb(null,results);
        })
        .catch(err=>{
            cb(err);
        });        
    });
    task.push((cb)=>{
        //为了排除雪球'观察'列表中的股票不被删除掉
        xueqiuGetJson('https://stock.xueqiu.com/v5/stock/portfolio/list.json',
        (err,json)=>{
            if(!err && json){
                if(json.data && json.data.stocks && json.data.stocks.length>0){
                    for(let c of json.data.stocks){
                        if(c.name=='观察'){
                            xueqiuGetJson(`https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=${c.id}&category=1`,
                            (err,json)=>{
                                if(!err && json && json.data && json.data.stocks){
                                    let map2 = {};
                                    for(let s of json.data.stocks){
                                        map2[s.symbol] = s;
                                    }
                                    cb(null,map2);
                                    return;
                                }
                                cb('获取xueqiu“观察”分组失败.2',err,json);
                            });
                            return;
                        }
                    }
                }
            }
            cb('获取xueqiu“观察”分组失败.1',err,json);
        });
    });
    task.push((cb)=>{
        //ttm>0 <200,股价在5日均线上方,k15涨势最好的前50只股票
        query(`SELECT name,code,category,ttm,price,ma5diff,ma10diff,ma20diff,ma30diff,k15_max FROM company_select  WHERE ttm>0 AND ttm<200 AND ma5diff>0  ORDER BY k15_max DESC LIMIT 50 `)
        .then(results=>{
            cb(null,{name:'MACD15',results});
        })
        .catch(err=>{
            cb(err);
        });
    }); 
    task.push((cb)=>{
        //ttm>0 <200,股价在5日均线上方,k60涨势最好的前50只股票
        query(`SELECT name,code,category,ttm,price,ma5diff,ma10diff,ma20diff,ma30diff,k60_max FROM company_select WHERE ttm>0 AND ttm<200 AND ma5diff>0 ORDER BY k60_max DESC LIMIT 50 `)
        .then(results=>{
            cb(null,{name:'MACD60',results});
        })
        .catch(err=>{
            cb(err);
        });
    });
    task.push((cb)=>{
        //ttm>0 <200,股价在5日均线上方,k15涨势最好的前50只股票会做惩罚
        query(`SELECT name,code,category,ttm,price,ma5diff,ma10diff,ma20diff,ma30diff,k60_max FROM company_select WHERE ttm>0 AND ttm<200 AND ma5diff>0 ORDER BY strategy1 DESC LIMIT 50 `)
        .then(results=>{
            cb(null,{name:'MAX15',results});
        })
        .catch(err=>{
            cb(err);
        });
    });     
    async.series(task,(err,results)=>{
        if(err){
            console.error(err);
            if(done)done();
            return;
        }
        
        let map2simple = {};
        for(let c of results[0]){
            map2simple[c.name] = c.simple;
        }
        let map2observed = results[1];
        let tops = [];
        let code2tops = {};
        //合并不同策略搜索出来的列表
        for(let i=2;i<results.length;i++){
            let R = results[i];
            if(R && R.name && R.results){
                for(let it of R.results){
                    if(!code2tops[it.code])
                        code2tops[it.code] = it;
                    let IT = code2tops[it.code];
                    if(IT.xueqiuCategory){
                        IT.xueqiuCategory += `,${R.name}`;
                    }else{
                        IT.xueqiuCategory = R.name;
                    }
                }
            }else{
                console.error('merge tops ',R);
            }
        }
        for(let k in code2tops){
            tops.push(code2tops[k]);
        }
        //这里将任务搜索出来的股票合并到tops中去
        xueqiuGetJson('https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1',
        (err,json)=>{
            if(err){
                if(done)done();
                return;
            }

            let tasks = [];
            let xueiquSet = {};
            let topSet = {}
            for(let a of json.data.stocks){
                xueiquSet[a.symbol] = 1;
            }
            for(let a of tops){
                topSet[a.code] = 1;
            }
            for(let s of tops){
                s.symbol = s.code;
                if(!xueiquSet[s.symbol]){ //不在雪球列表，加入
                    //add
                    console.log('ADD',s.name,s.symbol);
                    tasks.push(addStock(s.symbol));
                }
            }
            for(let s of json.data.stocks){
                if(!topSet[s.symbol] && !map2observed[s.symbol]){ //雪球列表中的不在榜上，删除(但是要排除观察表中的)
                    //delete
                    console.log('DELETE',s.name,s.symbol);
                    tasks.push(deleteStock(s.symbol));
                }
            }
            async.series(tasks,(err,results)=>{
                if(err){
                    console.error(err);
                    if(done)done();
                    return;
                }
                //进行分类
                let groups = {};
                for(let s of tops){
                    let g = {group:[]};
                    groups[s.code] = g;

                    if(s.ma30diff<0)
                        insertGroup(g,'MA30');
                    else if(s.ma20diff<0)
                        insertGroup(g,'MA20');
                    else if(s.ma10diff<0)
                        insertGroup(g,'MA10');
                    else if(s.ma5diff<0)
                        insertGroup(g,'MA5');
                    else
                        insertGroup(g,'MA0');

                    if(map2observed[s.symbol]) //观察组中的股票不变
                        insertGroup(g,'观察');
                    if(s.xueqiuCategory)
                        insertGroup(g,s.xueqiuCategory);
                }
                let task = [];
                for(let s of tops){
                    let g = groups[s.code];
                    if(g.groupNeedUpdate)
                        task.push(groupStock(g.group,s.name,s.code));
                }
                async.series(task,(err,results)=>{ //并行xueqiu会出问题(重复的分类)
                    if(err)console.error(err);
                    console.log('update_xueqiu DONE');
                    if(done)done();
                });
            });
        });
    });
}

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
                                        //fixbug:分类的股票不在全部之中
                                        if(!mapSymbol2Stock[s.symbol]){
                                            s.group = [];
                                            mapSymbol2Stock[s.symbol] = s;
                                            stocks.push(s);
                                        }
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
            console.log(`===== ${t.getHours()}:${lastMinutes} =====`)
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
        let r = data.item.map((it)=>{
            return it[macdidx];
        }).reverse();
        return r;
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
        if( (m[0]-m[1]) > -m[0] ){ //略微提前一点
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
    try{
        for(let it of t){
            m[it[k]] = it;
        }    
    }catch(e){
        console.error(e,t,k);
    }
    return m;
}
function removeGroup(s,name){
    let i = s.group.indexOf(name);
    if(i>=0){
        s.group.splice(i,1);
        s.groupNeedUpdate = true;
        return true;
    }
    return false;
}
function insertGroup(s,name){
    if(s.group.indexOf(name)==-1){
        s.group.push(name);
        s.groupNeedUpdate = true;
        return true;
    }
    return false;
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
            try{
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
            let task = [];
            for(let s of stocks){ //重置
                s.groupNeedUpdate = false;
                removeGroup(s,`U${n}`);//分类中D,U上的股票都要清除
                removeGroup(s,`D${n}`);
            }
            while(i--){
                let s = kc[i];
                if(!symbol2sc[s.symbol]){//如果不在sc表中,删除
                    kc.splice(i,1);//分类中的删除
                    removeGroup(s,`K${n}`); //这只股票将不在该组中了
                    insertGroup(s,`D${n}`); //下榜
                }
            }
            for(let s of sc){
                //如果不在kc表中,加入
                if(!symbol2kc[s.symbol]){
                    kc.push(s);//分类中添加
                    insertGroup(s,`K${n}`);
                    insertGroup(s,`U${n}`); //上榜
                }
            }
            //调整需要变动的分组
            for(let s of stocks){
                if(s.groupNeedUpdate)
                    task.push(groupStock(s.group,s.name,s.symbol)); //调整分组
            }
            
            async.series(task,(err,results)=>{
                if(err)console.error(err);
                let t = new Date();
                console.log(`===== DONE ${t.getHours()}:${t.getMinutes()}=====`);
            });
            }catch(e){
                console.error(e);
            }
        });
    }else{
        console.error(`Can't found category K${n}`);
    }
}

update_xueqiu_list(15,(err)=>{
    //不管数据库部分操作是否成功，列表中都可以进行继续监控
    watchMainLoop();
});

module.exports = {watchMainLoop};
