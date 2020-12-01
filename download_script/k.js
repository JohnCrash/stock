const mysql   = require('mysql');
const Crawler = require("crawler");
const async = require("async");
const bigint = require("big-integer");
const config = require("./config");
/**
 * FIXBUG: "Client does not support authentication protocol requested by server"
 * ALTER USER 'root'@'localhost' IDENTIFIED BY 'your new password'; 
 * ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your new password';
 */
var connection = mysql.createPool({
    connectionLimit : 30,
    host     : 'localhost',
    port    : config.port,
    user     : config.user,
    password : config.password,
    database : config.database
  });

  function dateString(date){
    if(typeof(date)==='object')
        return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
    else if(typeof(date)==='string'){
        let d = new Date(date);
        return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`;
    }else
        return 'null';    
  }

  /**
   * 遍历公司的k数据
   * id公司id,kstart起始日期
   * trader_callback 交易者回调
   *    每个k数据都会给trader_callback,并且给交易函数sell
   * 使用举例
   *  k_company(134,'2019-3-8','tech_macd',(k,sell)=>{
   *    ...
   *  }).then(results=>{
   *    ...
   *  });
   */
function k_company(id,kstart,db,trader_callback){
    return new Promise((resolve,reject)=>{
        let t0 = Date.now();
        let lastSellDate;
        function sell(buy,sell,max){
            if(buy && sell){
                let buy_value = buy.close;
                let sell_value = sell.close;
                let max_value = max.close;
                let dd = Math.floor((sell.date-buy.date)/(3600*24*1000));
                let max_dd = Math.floor((max.date-buy.date)/(3600*24*1000));
                //每年股市开盘时间为243天
                let rate = ((sell_value-buy_value))/(buy_value);
                let max_rate = ((max_value-buy_value))/(buy_value);
                lastSellDate = sell.date;
                let sqlstr = `insert ignore into ${db} values (${id},'${dateString(buy.date)}','${dateString(sell.date)}',${buy_value},${sell_value},${rate},${dd},'${dateString(max.date)}',${max_rate},${max_dd},${max_value})`;
    
                connection.query(sqlstr,(error, results, field)=>{
                    if(error)console.error(id,error);
                });
            }
        }
        let startDate = dateString(new Date(kstart));
        connection.query(`select date,open,close,macd from kd_xueqiu where id=${id} and date>='${startDate}'`,(error, results, field)=>{
            if(error){
                console.error(id,error);
                reject(error);
            }else{
                for(let it of results){
                    trader_callback(it,sell);
                }
                if(results.length>0){
                    resolve({
                        beginDate:results[0].date,
                        endDate:results[results.length-1].date,
                        lastSellDate,
                        usetime:Date.now()-t0
                    });
                }else{
                    resolve({usetime:Date.now()-t0});
                }
            }   
        });
    });
}
/**
 * 做一个全部公司都要做的任务
 * 函数举例
 * companys_task().then((results)=>{
 *  
 * }).catch(err=>{
 * 
 * })
 */
function companys_task(itemStr,task){
    return new Promise((resolve,reject)=>{
        let t0 = Date.now();
        connection.query(`select ${itemStr?itemStr:"*"} from company where \`ignore\` is null`,(error, results, field)=>{
            if(error){    
                console.error(error);
                reject(error);
            }else{
                let tasks = [];
                for(let com of results){
                    tasks.push(task(com,connection));
                }
                async.series(tasks,(err,result)=>{
                    if(err){
                        reject(error);
                    }else{
                        resolve(Date.now()-t0);
                    }
                })
            } 
        });
    });
}

/**
 * 并行公司任务
 */
function paralle_companys_task(itemStr,n,task){
    return new Promise((resolve,reject)=>{
        let t0 = Date.now();
        connection.query(`select ${itemStr?itemStr:"*"} from company`,(error, results, field)=>{
            if(error){    
                console.error(error);
                reject(error);
            }else{
                let tasks = [];
                for(let com of results){
                    tasks.push(task(com,connection));
                }
                async.parallelLimit(tasks,n,(err,result)=>{
                    if(err){
                        reject(error);
                    }else{
                        resolve(Date.now()-t0);
                    }
                })
            } 
        });
    });
}

/**
 * 雪球更新用
 */
function companys_task_continue(itemStr,n,task){
    return new Promise((resolve,reject)=>{
        let t0 = Date.now();
        connection.query(`select ${itemStr?itemStr:"*"} from company`,(error, results, field)=>{
            if(error){    
                console.error(error);
                reject(error);
            }else{
                //如果kd_xueqiu数据已经更新就不进行处理了
                connection.query(`select distinct id from kd_xueqiu where date='${dateString(new Date())}'`,(err,res,fie)=>{
                    if(err){
                        console.error(err);
                        reject(err);
                    }else{
                        let tasks = [];
                        let has = {};
                        for( let r of res){
                            has[r.id] = true;
                        }
                        for(let com of results){
                            if( !has[com.id] ) //已经存在的就不进行更新了
                                tasks.push(task(com,connection));
                        }
                        console.info('需要更新：',tasks.length,'只股票信息')
                        if(tasks.length>0)
                            async.parallelLimit(tasks,n,(err,result)=>{
                                if(err){
                                    reject(error);
                                }else{
                                    resolve(Date.now()-t0);
                                }
                            });                    
                        else
                            resolve(Date.now()-t0);
                    }
                });
            } 
        });
    });
}

function companys_task_continue2(itemStr,n,task){
    let cur = new Date();
    let dd =cur.getDate();
    function flagit(com){
        if(cur.getHours()>=15){ //三点后更新才加标记
            connection.query(`update company set \`ignore\`=${dd} where id=${com.id}`,(error, results, field)=>{
                if(error)console.error(error);
            });
        }
    }    
    return new Promise((resolve,reject)=>{
        let t0 = Date.now();
        connection.query(`select ${itemStr?itemStr:"*"} from company where \`ignore\`!=${dd} or \`ignore\` is null`,(error, results, field)=>{
            if(error){    
                console.error(error);
                reject(error);
            }else{
                let tasks = [];
                for(let com of results){
                    tasks.push(task(com,flagit));
                }
                console.info('需要更新：',tasks.length,'只股票信息')
                if(tasks.length>0)
                    async.parallelLimit(tasks,n,(err,result)=>{
                        if(err){
                            reject(error);
                        }else{
                            resolve(Date.now()-t0);
                        }
                    });                    
                else
                    resolve(Date.now()-t0);
            } 
        });
    });
}

function query(querys){
    let queryArray = (typeof(querys)==='object' && query.length) ? querys : arguments;
    return new Promise((resolve,reject)=>{
        let tasks = [];
        for(let str of queryArray){
            tasks.push((cb)=>{
                connection.query(str,(error,results,field)=>{
                    if(error){
                        cb(error);
                    }else{
                        cb(null,results);
                    }
                });        
            });    
        }
        async.series(tasks,(err,result)=>{
            if(err)
                reject(err);
            else{
                if(result.length==1)
                    resolve(result[0]);
                else
                    resolve(result);
            }
        })
    });
}
/**
 * 将每一年的一只股票的数据统计到表sta_macd_year中去。
 * 基于tech_macd表中的数据
 */
const sta_macd_names = ['company_id','year','category','income','positive_income',
    'negative_income','static_income','opertor_num','positive_num','negative_num','usage_rate','hold_day'];
function macd_year_company(id,category,year,cb){
    connection.query(`select * from tech_macd where company_id=${id}`+(year?` and sell_date>='${year}-1-1'`:''),(error, results, field)=>{
        if(error){
            console.error(error);
            cb(error);
            return;
        }
        let m = [];
        for(let i in results){
            let it = results[i];
            let y = it.sell_date.getFullYear();
            if(!m[y]){
                m[y] = {income:0,positive_income:0,negative_income:0,static_income:0,
                    opertor_num:0,positive_num:0,negative_num:0,usage_rate:0,hold_day:0};
            }
            m[y].income += it.rate;
            if(it.rate>0){
                m[y].positive_income += it.rate;
                m[y].positive_num++;
            }else{
                m[y].negative_income += it.rate;
                m[y].negative_num++;
            }
            m[y].opertor_num++;
            m[y].hold_day+=it.rate_dd;
            m[y].id = it.company_id;
        }
        for(let i in m){
            let c = m[i];
            if(i==year){
                let args = [c.id,i,category,c.income,c.positive_income,c.negative_income,c.static_income,c.opertor_num,c.positive_num,c.negative_num,c.usage_rate,c.hold_day];
                let argument_list = [];
                for(let i in sta_macd_names){
                    argument_list.push(`${sta_macd_names[i]}=${args[i]}`);
                }
                connection.query(`update sta_macd_year set ${argument_list.join(',')} where company_id=${id} and year=${year}`,(error)=>{
                    if(error)
                        console.error(error);
                });    
            }else{
                connection.query(`insert ignore into sta_macd_year values (${c.id},${i},${category},${c.income},${c.positive_income},${c.negative_income},${c.static_income},${c.opertor_num},${c.positive_num},${c.negative_num},${c.usage_rate},${c.hold_day})`,(error)=>{
                    if(error)
                        console.error(error);
                });    
            }
        }
        cb(error);
    });
}
/**
 * 计算sta_macd_year，用于年收益率分布与年收益率
 */
function macd_year(){
    console.log('handle macd_year...');
    connection.query('select max(year) as year from sta_macd_year',(error, results, field)=>{
        if(error){
            console.error(error);
        }else{
            if(results.length>0){
                let year = results[0].year;
                connection.query('select id,category from company where \`ignore\` is null',(error, results, field)=>{
                    if(error){
                        console.error(error);
                    }else{
                        let a = [];
                        for(let i=0;i<results.length;i++){
                            let it = results[i];
                            a.push(function(cb){
                                console.log(it.id);
                                macd_year_company(it.id,it.category,year,(error)=>{
                                    cb(error);
                                });
                            });
                        }  
                        async.series(a,(err, results)=>{
                            if(!err){
                                macd_wave()
                            }else console.error(err);
                        });
                    }
                });
            }else{
                console.error(`select max(year) as year from sta_macd_year return results.length = ${results}`);
            }
        }
    });
}

function macd_wave(){
    console.log('handle macd_wave...')
    connection.query('select max(date) as d from sta_macd_wave',(error, results, field)=>{
        if(error){
            console.error(error);
        }else{
            if(results.length>0){
                let d = results[0].d;
                let b = new Date(dateString(new Date(d?d:'1990-1-1')));
                let e = new Date(dateString(new Date()));
                //这里使用日SH000001的k的日期，因为星期天和节日没有成交数据
                connection.query('select date from kd_xueqiu where id=8828 order by date',(error, results, field)=>{
                    if(error){
                        console.error(error);
                        return;
                    }
                    let tasks = [];
                    for(let dd of results){
                        let cc = new Date(dd.date);
                        if(cc>=b && cc<=e){
                            let date = dateString(cc);
                            tasks.push((cb)=>{
                                async.parallel([(cb)=>connection.query(`select count(company_id) as sell from tech_macd where sell_date='${date}'`,(error, results, field)=>{
                                    cb(error,results);
                                }),
                                (cb)=>connection.query(`select count(company_id) as buy from tech_macd where buy_date='${date}'`,(error, results, field)=>{
                                    cb(error,results);
                                })],(error,result)=>{
                                    if(error){
                                        console.error(error); //如果出错需要删除sta_macd_wave重新执行
                                    }else{
                                        let sell = result[0][0].sell;
                                        let buy = result[1][0].buy;
                                        connection.query(`insert ignore into sta_macd_wave values ('${date}',${buy},${sell})`,(error, results, field)=>{
                                            if(error)console.error(error); //如果出错需要删除sta_macd_wave重新执行
                                            console.log(date,buy,sell);
                                            cb(error);
                                        });
                                    }
                                });
                            });
                        }
                    }
                    async.series(tasks,(err,result)=>{
                        console.log(err,'DONE!');     
                    });
                });
            }else{
                console.error(`select max(date) as d from sta_macd_wave return results.length<=0`);
            }
        }
    });
}

function xueqiuGetJson(uri,cb){
    let c = new Crawler({
        maxConnections : 1,
        callback : function(error, res, done){
            if(error)console.error(error);
            try{
                let sl = JSON.parse(res.body);
                if(sl.error_code=="0" || sl.success){
                    cb(null,sl);
                }else{
                    console.error(sl.error_code,sl.error_description,uri);
                    console.log(res.body);
                    cb(sl);                    
                }
            }catch(e){
                console.error(e);
                cb(e);
            }
            
            done();
        }
    });    
    c.queue({
        uri,
        jQuery: false,
        headers:{
            Cookie:xuequeCookie
        }
    });
}

function xueqiuPostJson(uri,form,cb){
    let c = new Crawler({
        maxConnections : 1,
        callback : function(error, res, done){
            if(error)console.error(error);
            try{
                let sl = JSON.parse(res.body);
                if(sl.error_code=="0" || sl.success){
                    cb();
                }else{
                    console.error(sl.error_code,sl.error_description,uri);
                    console.log(res.body);
                    cb(sl);                    
                }
            }catch(e){
                console.error(e);
                cb(e);
            }
            
            done();
        }
    });    
    c.queue({
        uri,
        jQuery: false,
        headers:{
            Cookie:xuequeCookie
        },
        method:'POST',
        form
    });
}

var xuequeCookie = ""
function getXueqiuCookie(){
    return xuequeCookie
}
//获取xueqiu网站的cookie
function initXueqiuCookie(cb){
    if(cb && xuequeCookie.length>0){
        cb(true,xuequeCookie)
        return
    }
    uri = "https://xueqiu.com/"
    let c = new Crawler({
        maxConnections : 1,
        callback : function(error, res, done){
            if(error)console.error(error);
            if(res.statusCode==200){
                cookie = "";
                for( it of res.headers['set-cookie']){
                    c = it.substr(0,it.search(';'))
                    if(c.substr(-1)!="="){
                        cookie += c
                        if(cookie!="")
                            cookie += "; "
                    }                        
                }
                xuequeCookie = cookie
                if(cb){
                    cb(true,cookie)
                }
            }else{
                console.error("xueqiuCookie",res.statusCode,res.boday);
                if(cb)
                    cb(false,null)
            }
            done();
        }
    });    
    c.queue({
        uri:uri
    });
}
//macd_all();
//macd_year();
//macd_wave();

module.exports = {k_company,companys_task,dateString,query,connection,companys_task_continue2,
    paralle_companys_task,xuequeCookie,xueqiuPostJson,xueqiuGetJson,companys_task_continue,initXueqiuCookie,getXueqiuCookie};