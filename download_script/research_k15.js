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
const {update_company} = require('./desc');

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

function calcgain_MAX(k0,macd0,N,r){
    let lastK;
    let lastM;
    let buyK;
    let buyI;
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
                buyI = Math.floor(i/N);
            }else if(buyK && m<0){
                //trade(buyK,v);
                if(buyI != Math.floor(i/N) && maxK>0){//交易在一天内进行将被排除
                    let r = maxK/buyK;

                    gain = gain*r;
    
                    if(r<1){
                        acc += (1-r);
                    }else{
                        if(acc>maxdrawal)maxdrawal = acc;
                        acc = 0;
                    }    
                } 
                buyI = undefined;
                buyK = undefined;
                maxK = 0;
            }
        }
        if(buyK && v>maxK && buyI != Math.floor(i/N))maxK = v;
        lastK = v;
        lastM = m;
    }
    if(acc>maxdrawal)maxdrawal = acc;
    return [gain,maxdrawal>0?(gain-1)/maxdrawal:(gain-1)/0.1];
}

function bookmarkTask(k,bookmark,total,top){
    return (cb)=>{
        query(`SELECT name,code,category,${k} FROM stock.company_select where static60>=1 and static30>1 order by ${(k==='k15_max'?(`(k15_max+k30_max+k60_max)/3`):k)} desc limit ${total}`).then(companys=>{
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

        '化学原料和化学制品制造业':'原料',
        '石油加工、炼焦和核燃料加工业':'原料',
        '橡胶和塑料制品业':'原料',
        '有色金属冶炼和压延加工业':'原料',
        '造纸和纸制品业':'原料',
        '非金属矿物制品业':'原料',
        '化学原料':'原料',
        '有色金属矿采选业':'原料',
        '水的生产和供应业':'原料',
        '化学纤维制造业':'原料',
        '黑色金属冶炼和压延加工业':'原料',
        '金属制品':'原料',
        '钢铁':'原料',
        '林业':'原料',
        '渔业':'原料',
        '采掘服务':'原料',
        '煤炭开采和洗选业':'原料',

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

        '燃气生产和供应业':'能源',
        '电力、热力生产和供应业':'能源',
        '生态保护和环境治理业':'能源',
        '电力':'能源',

        '计算机、通信和其他电子设备制造业':'科技',
        '计算机应用':'科技',
        '半导体':'科技',
        '通信设备':'科技',
        '软件和信息技术服务业':'科技',
        '互联网和相关服务':'科技',

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
function update_xueqiu(){
    //首先下载雪球的股票列表，然后删除不在榜的。加入上榜的。然后重新分类
    query(`SELECT name,code,category,k15_max,price,ma5diff,ma10diff,ma20diff,ma30diff FROM stock.company_select where bookmark15=1`).then(tops=>{
        xueqiuGetJson('https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1',
        (err,json)=>{
            if(err)return;

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
            async.parallelLimit(tasks,5,(err,results)=>{
                if(err)console.error(err);
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

                    groups[s.code].push(mapCategory(s.category));
                }
                let task = [];
                for(let s of tops){
                    task.push(groupStock(groups[s.code],s.name,s.code));
                }
                async.series(task,(err,results)=>{
                    if(err)console.error(err);
                    console.log('update_xueqiu DONE');
                });
            });
        });
    }).catch(err=>{
        console.error(err);
    });
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
                let [k15_max,k15_maxdrawal] = calcgain_MAX(k15close,macd15,16);
                let [k30_max,k30_maxdrawal] = calcgain_MAX(k30close,macd30,8);
                let [k60_max,k60_maxdrawal] = calcgain_MAX(k60close,macd60,4);
                let [k120_max,k120_maxdrawal] = calcgain_MAX(k120close,macd120,2);
                let [kd_max,kd_maxdrawal] = calcgain_MAX(kdclose,macdday,1);


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
            //task.push(bookmarkTask('k120_max','bookmark120',300,5));
            //task.push(bookmarkTask('kd_max','bookmarkd',300,5));
            async.series(task,(err,results)=>{
                console.log('research_k15 DONE!');
                update_xueqiu();
                if(done)done();
            });
        });
    }).catch(err=>{
        console.error(err);
        if(done)done(err);
    });    
}

update_xueqiu();
//research_k15();
module.exports = {research_k15};