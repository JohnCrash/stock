/**
 * 对精选出来的热点股票进行跟踪
 */
const {companys_task,k_company,dateString,query,connection,
    xuequeCookie,xueqiuPostJson,xueqiuGetJson} = require('./k');
const async = require('async');
const macd = require('macd');

function mapCategory(cat){
    const cat2 = {
        '互联网传媒':'传媒',
        '电信、广播电视和卫星传输服务':'传媒',
        '新闻和出版业':'传媒',
        '文化艺术业':'传媒',
        '广播、电视、电影和影视录音制作业':'传媒',
        '文教、工美、体育和娱乐用品制造业':'传媒',

        '酒、饮料和精制茶制造业':'吃喝',
        '食品加工':'吃喝',
        '餐饮':'吃喝',
        '畜禽养殖':'吃喝',
        '农副食品加工业':'吃喝',
        '医药制造业':'吃喝',
        '化学制药':'吃喝',
        '餐饮业':'吃喝',
        '农业':'吃喝',
        '动物保健':'吃喝',
        '中药':'吃喝',

        '化学原料和化学制品制造业':'原料',
        '石油加工、炼焦和核燃料加工业':'原料',
        '橡胶和塑料制品业':'原料',
        '有色金属冶炼和压延加工业':'原料',
        '造纸和纸制品业':'原料',
        '非金属矿物制品业':'原料',
        '化学原料':'原料',
        '有色金属矿采选业':'原料',
        '水的生产和供应业':'原料',
        '化学纤维':'原料',
        '化学纤维制造业':'原料',
        '黑色金属冶炼和压延加工业':'原料',
        '金属制品':'原料',
        '钢铁':'原料',
        '林业':'原料',
        '渔业':'原料',
        '采掘服务':'原料',
        '煤炭开采和洗选业':'原料',
        '化学制品':'原料',

        '银行':'金融',
        '商务服务业':'金融',
        '贸易':'金融',
        '资本市场服务':'金融',
        '房地产业':'金融',
        '房地产开发':'金融',
        '其他金融业':'金融',
        '土木工程建筑业':'金融',
        '建筑装饰和其他建筑业':'金融',
        '房屋建设':'金融',
        '保险':'金融',
        '多元金融':'金融',
        '证券':'金融',

        '燃气生产和供应业':'能源',
        '电力、热力生产和供应业':'能源',
        '生态保护和环境治理业':'能源',
        '电力':'能源',
        '高低压设备':'能源',

        '计算机、通信和其他电子设备制造业':'科技',
        '计算机应用':'科技',
        '半导体':'科技',
        '通信设备':'科技',
        '软件和信息技术服务业':'科技',
        '互联网和相关服务':'科技',
        "其他电子":'科技',
        "计算机设备":'科技',
        "电子制造":'科技',

        '通用设备制造业':'制造',
        '金属制品业':'制造',
        '铁路、船舶、航空航天和其他运输设备制造业':'制造',
        '专用设备制造业':'制造',
        '仪器仪表制造业':'制造',
        '其他制造业':'制造',
        '家具制造业':'制造',
        '工业金属':'制造',
        '电机':'制造',
        '电气机械和器材制造业':'制造',
        '白色家电':'制造',
        '汽车制造业':'制造',
        '服装家纺':'制造',
        '纺织业':'制造',
        '汽车整车':'制造',
        '船舶制造':'制造',
        '纺织服装、服饰业':'制造',
        '地面兵装':'制造',
        '电气自动化设备':'制造',
        '纺织制造':'制造',
        '电源设备':'制造',
        '光学光电子':'制造',
        '专用设备':'制造',

        '零售业':'其他',
        '批发业':'其他',
        '租赁业':'其他',    
        '综合':'其他',  
        '仓储业':'其他',  
        '包装印刷':'其他',
        '公共设施管理业':'其他',
        '港口':'其他',
        '水上运输业':'其他',
        '专业技术服务业':'其他',
        '管道运输业':'其他',
        '装卸搬运和运输代理业':'其他',
        '环保工程及服务':'其他',
        'null':'其他',
    }
    if(cat2[cat]){
        return cat2[cat];
    }else{
        console.error('为分类的',cat);
        return '其他';
    }
}

/**
 * 使用bookmark15更新雪球上的股票
 */
function update_xueqiu_list(lv,done){
    //首先下载雪球的股票列表，然后删除不在榜的。加入上榜的。然后重新分类
    query(`SELECT name,code,category,k${lv}_max,price,ma5diff,ma10diff,ma20diff,ma30diff FROM stock.company_select where bookmark${lv}=1`).then(tops=>{
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
                if(!topSet[s.symbol]){ //雪球列表中的不在榜上，删除
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
                    groups[s.code] = [];

                    if(s.ma30diff<0)
                        groups[s.code].push('MA30');
                    else if(s.ma20diff<0)
                        groups[s.code].push('MA20');
                    else if(s.ma10diff<0)
                        groups[s.code].push('MA10');
                    else if(s.ma5diff<0)
                        groups[s.code].push('MA5');
                    else
                        groups[s.code].push('MA0');

                    groups[s.code].push(mapCategory(s.category));
                }
                let task = [];
                for(let s of tops){
                    task.push(groupStock(groups[s.code],s.name,s.code));
                }
                async.series(task,(err,results)=>{ //并行xueqiu会出问题(重复的分类)
                    if(err)console.error(err);
                    console.log('update_xueqiu DONE');
                    if(done)done();
                });
            });
        });
    }).catch(err=>{
        console.error(err);
        if(done)done(err);
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
                                        it.stocks.push(mapSymbol2Stock[s.symbol]);
                                        //fixbug:分类的股票不在全部之中
                                        if(!mapSymbol2Stock[s.symbol]){
                                            s.group = [];
                                            mapSymbol2Stock[s.symbol] = s;
                                            stocks.push(s);
                                        }
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
    for(let it of t){
        m[it[k]] = it;
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
    if(!err)
        watchMainLoop();
});

module.exports = {watchMainLoop};
