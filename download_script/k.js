const mysql   = require('mysql');
const Crawler = require("crawler");
const async = require("async");
const bigint = require("big-integer");

/**
 * FIXBUG: "Client does not support authentication protocol requested by server"
 * ALTER USER 'root'@'localhost' IDENTIFIED BY 'your new password'; 
 * ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your new password';
 */
var connection = mysql.createPool({
    connectionLimit : 30,
    host     : 'localhost',
    port    : 3307,
    user     : 'root',
    password : '789',
    database : 'stock'
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
        headers:{
            Cookie:xuequeCookie
        },
        method:'POST',
        form
    });
}
//macd_all();
//macd_year();
//macd_wave();
/*
var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; __utmz=1.1547831580.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.2077977505.1548294644; aliyungf_tc=AQAAAHwGH12l3ggA8M92e+oJhqNBY38L; xq_a_token=8dd2cc84915c45983930bb32e788dc93e0fcfddd; xq_a_token.sig=rjG2G1sq6nNdwvwGHxpwqDYbk3s; xq_r_token=5bb4c968b369150a382906ceba61eb8763282a13; xq_r_token.sig=eoelFajTh7zpqBNrEdBVD9rYjbw; u=661548299105754; Hm_lvt_1db88642e346389874251b5a1eded6e3=1548039323,1548194617,1548294644,1548299106; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1548299113; __utma=1.564054628.1547831580.1548294646.1548299113.13; __utmc=1; __utmt=1; __utmb=1.1.10.1548299113';
*/
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.2077977505.1548294644; xq_a_token=8dd2cc84915c45983930bb32e788dc93e0fcfddd; xq_a_token.sig=rjG2G1sq6nNdwvwGHxpwqDYbk3s; xq_r_token=5bb4c968b369150a382906ceba61eb8763282a13; xq_r_token.sig=eoelFajTh7zpqBNrEdBVD9rYjbw; Hm_lvt_1db88642e346389874251b5a1eded6e3=1548294644,1548299106,1548375753,1548463656; _gat_gtag_UA_16079156_4=1; u=721548463656672; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1548463660';
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.209931511.1550060636; xq_a_token=340cd8594a60098b3a9101bfed3c937ef2a41ae3; xq_a_token.sig=X5wPD5esioe_4cV4REojaNVJuMg; xq_r_token=9b4eeb50e2b16a45217033dcc55df006837cff00; xq_r_token.sig=Y3KOMJ2JkHB5ccV0Re2uvclcddY; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550060636,1550127249,1550203847,1550237793; u=441550237793218; _gat_gtag_UA_16079156_4=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550237806';
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.209931511.1550060636; xq_a_token=340cd8594a60098b3a9101bfed3c937ef2a41ae3; xq_a_token.sig=X5wPD5esioe_4cV4REojaNVJuMg; xq_r_token=9b4eeb50e2b16a45217033dcc55df006837cff00; xq_r_token.sig=Y3KOMJ2JkHB5ccV0Re2uvclcddY; u=741550318108222; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550203847,1550237793,1550285970,1550318108; _gat_gtag_UA_16079156_4=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550321763';
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.209931511.1550060636; xq_a_token=340cd8594a60098b3a9101bfed3c937ef2a41ae3; xq_a_token.sig=X5wPD5esioe_4cV4REojaNVJuMg; xq_r_token=9b4eeb50e2b16a45217033dcc55df006837cff00; xq_r_token.sig=Y3KOMJ2JkHB5ccV0Re2uvclcddY; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550237793,1550285970,1550318108,1550399051; u=561550399050848; _gat_gtag_UA_16079156_4=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550399365';
//var xuequeCookie = 'xq_a_token=0d73a36f00a0e985d381412742c39d12fb3ca56a; xq_a_token.sig=knknlVAPG2nkQ9enLy6gnEylv5w; xq_r_token=18d38484159ce73ae3451797d6517a41efa531b1; xq_r_token.sig=_SVEXsDz6FhNpFjXlGS8TPj_T7Q; _ga=GA1.2.1181448870.1550643624; _gid=GA1.2.230571212.1550643624; _gat=1; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550643624; u=291550643626655; s=ds11jo7273; device_id=c23e116dd6bed04938f77815772ad027; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550643643';
//var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=e7120e4e7b4be743f2c74067a44ee0e628770830; xq_a_token.sig=hE4WTsbi-zbUt506L09ZZbdJ_kI; xqat=e7120e4e7b4be743f2c74067a44ee0e628770830; xqat.sig=8PcFgZlZW0v0IH8MsTl27E3deIY; xq_r_token=be060178b1ebd6fa09c111bfbdd3b40db9e98dfc; xq_r_token.sig=WpxrkUwRX5LASIPyFu-1kPlaCJs; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; _gid=GA1.2.364037776.1551618045; aliyungf_tc=AQAAAIRMQWu3EQ4ACsd2e0ZdK3tv9E1U; Hm_lvt_1db88642e346389874251b5a1eded6e3=1551674476,1551680738,1551754280,1551766767; __utma=1.430870872.1550643434.1551422478.1551766799.20; __utmc=1; __utmb=1.1.10.1551766799; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1551767644";
//var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; _gid=GA1.2.116983169.1552205760; xq_a_token=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xqat=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xq_r_token=fcc1b1e4ddfb2bc4d55bfcccff1ba4b36e0091ff; xq_is_login=1; u=6625580533; xq_token_expire=Thu%20Apr%2004%202019%2020%3A06%3A35%20GMT%2B0800%20(CST); aliyungf_tc=AQAAALeHCXbJlgEAnvGD3qvW+7mooFBG; Hm_lvt_1db88642e346389874251b5a1eded6e3=1552205761,1552219571,1552228090,1552267935; __utmc=1; snbim_minify=true; __utma=1.430870872.1550643434.1552267939.1552282682.34; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1552288329";
//var xuequeCookie = "_ga=GA1.2.1111103611.1552419115; device_id=86c74fff9e86b7e01e5ce82ff004b545; s=dv19wkbj3n; __utmz=1.1552420001.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jt678811; remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xq_a_token.sig=zppQy4QF65jt8GfChXPNjyMkWAo; xqat=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xqat.sig=jUSIhwzsNcYplGuru4r1DYPdx60; xq_r_token=fcc1b1e4ddfb2bc4d55bfcccff1ba4b36e0091ff; xq_r_token.sig=SDG-vOE8ZKBa2BPaOgKGZqU60wI; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; _gid=GA1.2.1540253122.1553437811; __utma=1.1111103611.1552419115.1552572870.1553450381.3; aliyungf_tc=AQAAAPxpu0ioJgUAh892e011QOiC3EV3; Hm_lvt_1db88642e346389874251b5a1eded6e3=1553511387,1553513323,1553513398,1553514817; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1553525764";
//var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; __utma=1.430870872.1550643434.1554355130.1554359168.59; _gid=GA1.2.1383760454.1554625060; remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=71b3c618ea93d9084a94f302fa8fb7fcc5ce488e; xq_a_token.sig=diLi_uvGEwT4OH-IPDoOKO5sNVc; xqat=71b3c618ea93d9084a94f302fa8fb7fcc5ce488e; xqat.sig=0r1b8KeeHV3W5hvOdMS7GSekOmU; xq_r_token=8fb597d0e41b710046ac912669d397d1b2540ed5; xq_r_token.sig=C6vMS7U6TzYGBbZm0PF4v41OrHs; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; aliyungf_tc=AQAAABAuy1a6igwAKEzxcmhkPQUp394u; _gat=1; Hm_lvt_1db88642e346389874251b5a1eded6e3=1554625060,1554630741,1554694918,1554707104; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1554707127";
//var xuequeCookie = "aliyungf_tc=AQAAANI3zXGVjAgALUzxcmiIaM6zMrmL; snbim_minify=true; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1555530797; __utmc=1; __utmz=1.1555526611.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); xqat=71b3c618ea93d9084a94f302fa8fb7fcc5ce488e; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; bid=693c9580ce1eeffbf31bb1efd0320f72_julkdswd; device_id=b2299f7a7a6e9fd1b6c3566893234fc7; remember=1; __utma=1.837257534.1555525216.1555526611.1555526611.1; xqat.sig=0r1b8KeeHV3W5hvOdMS7GSekOmU; xq_r_token.sig=C6vMS7U6TzYGBbZm0PF4v41OrHs; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; s=dz12qgm3hk; xq_a_token=71b3c618ea93d9084a94f302fa8fb7fcc5ce488e; _gat=1; xq_is_login=1; u=6625580533; _gid=GA1.2.96212437.1555525216; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; xq_r_token=8fb597d0e41b710046ac912669d397d1b2540ed5; _ga=GA1.2.837257534.1555525216; xq_a_token.sig=diLi_uvGEwT4OH-IPDoOKO5sNVc; Hm_lvt_1db88642e346389874251b5a1eded6e3=1555524655";
//var xuequeCookie = "_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; _gid=GA1.2.1266982273.1557213763; xqat=c8a01a11b97a55866707ca1e194228d7879567ef; xqat.sig=mLRz1b4uo_cZxG5yK4Ek0CxL5lM; xq_a_token=c8a01a11b97a55866707ca1e194228d7879567ef; xq_a_token.sig=4kezb12eUVNWEwd_HuCzkWAdkkI; xq_r_token=2b5c27dc7ec2171604a959c1784f549eeb5de858; xq_r_token.sig=T57018oz9Had4kZVOBnQEgmv0CY; __utma=1.528987204.1555945543.1556536504.1557235587.8; aliyungf_tc=AQAAADmCOi5CKwUANsd2e3pfzq5oqXln; Hm_lvt_1db88642e346389874251b5a1eded6e3=1556612192,1557055297,1557213763,1557246567; snbim_minify=true; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1557247855; _gat=1"
//var xuequeCookie = '_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; _gid=GA1.2.1266982273.1557213763; aliyungf_tc=AQAAAMypmRCTWwgANsd2e6obBihqHZWt; __utma=1.528987204.1555945543.1557235587.1557301168.9; __utmc=1; captcha_id=IsKBNNOQ5agIg9Odmkxiu3p2rBTSNC; captcha_id.sig=ITeB8D8WM981teXvtyIudYvOeO0; remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=c7127f4de8f16bf2bcd30b3031387de6260500cb; xq_a_token.sig=MIgATerRTHsE5DYaBHnuqqRFfFo; xqat=c7127f4de8f16bf2bcd30b3031387de6260500cb; xqat.sig=82Mg1id89QIIPUG7xoTJUwem_CQ; xq_r_token=3d33c80017c62235319c6f3b37963a1f0f37335f; xq_r_token.sig=PvEd3cudFCzP6VN_enu0XKenHrs; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; snbim_minify=true; Hm_lvt_1db88642e346389874251b5a1eded6e3=1557246567,1557291007,1557292743,1557304527; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1557309621'
//var xuequeCookie = '_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; __utma=1.528987204.1555945543.1559724555.1559800092.16; aliyungf_tc=AQAAAJxNJALzBQ0AF/CD3om5rmeUDAi4; Hm_lvt_1db88642e346389874251b5a1eded6e3=1559675740,1559724512,1559798842,1560156104; remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=1e101b8100d35fef37c40ec2c57ac3447de4349e; xq_a_token.sig=nBFPcEURxMS88Zo0GRh20ozkJWI; xqat=1e101b8100d35fef37c40ec2c57ac3447de4349e; xqat.sig=UoeOCQ7gb9CpH20OEKs1EYAPux4; xq_r_token=8d927130a226709a5cf09bb912144a76dcbe7e41; xq_r_token.sig=f5sXoDS-qYrwd1K0ZUkyhdCp13s; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1560156432';
//var xuequeCookie = '_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; __utma=1.528987204.1555945543.1560932700.1562722736.22; aliyungf_tc=AQAAAM67e2A/qAEAl/aD3rtLsJMnc3N9; Hm_lvt_1db88642e346389874251b5a1eded6e3=1562640314,1562722178,1562901691,1562914570; remember=1; xq_a_token=b125a692c32c04baa56dbbd5f7c707e0e24babb1; xqat=b125a692c32c04baa56dbbd5f7c707e0e24babb1; xq_r_token=f78d4cb16a43db4a69e5f29ed34c6e7e7d8b05d9; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1562926742'
//var xuequeCookie = '_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; aliyungf_tc=AQAAAOIpumBckAMAiQbzchVmEU+Ji7i7; __utmc=1; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; __utma=1.528987204.1555945543.1571234998.1573824873.28; Hm_lvt_1db88642e346389874251b5a1eded6e3=1574067809; acw_tc=2760822d15749152971941684e7f4320cc69616649eafea22bc5d90f26efbe; remember=1; xq_a_token=6ed8f0f9f30bc4f13f65bb3102333a0ead64c3ca; xqat=6ed8f0f9f30bc4f13f65bb3102333a0ead64c3ca; xq_r_token=aa3abe067eed22f1c36774dec016a669fa845891; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1575272484; snbim_minify=true'
//var xuequeCookie = '_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; __utmz=1.1555945599.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; aliyungf_tc=AQAAAOIpumBckAMAiQbzchVmEU+Ji7i7; __utmc=1; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; acw_tc=2760822d15756229262972757e6f293b44f4b01eff4ceb7a180f0a4c9ed067; Hm_lvt_1db88642e346389874251b5a1eded6e3=1577774083,1577774182,1577774249,1577774257; __utma=1.528987204.1555945543.1577775593.1577826553.72; remember=1; xq_a_token=c44d723738529eb6b274022a320258d92f31cc1e; xqat=c44d723738529eb6b274022a320258d92f31cc1e; xq_r_token=b926ebba0cf9dcf8c01a628b525f93191a24ca0d; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1577924260'
//var xuequeCookie = '_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; cookiesu=611580616600184; Hm_lvt_1db88642e346389874251b5a1eded6e3=1580196127,1580197850,1580447002,1580630322; remember=1; xq_a_token=0e0638737a1c6fc314110dbcfaca3650f71fce4b; xqat=0e0638737a1c6fc314110dbcfaca3650f71fce4b; xq_r_token=b2004307cb6bd998b245347262380833b61ce0f4; xq_is_login=1; u=6625580533; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1580630785'
//var xuequeCookie = "_ga=GA1.2.528987204.1555945543; device_id=3977a79bb79f8dd823919ae175048ee6; s=ds12dcnoxk; bid=693c9580ce1eeffbf31bb1efd0320f72_jushvajy; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; _gid=GA1.2.2101692300.1585791003; Hm_lvt_1db88642e346389874251b5a1eded6e3=1585824059,1585824478,1585826449,1585872476; remember=1; xq_a_token=b4d6d8d0ad043e0f4370c514bad3097678175362; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjY2MjU1ODA1MzMsImlzcyI6InVjIiwiZXhwIjoxNTg4NDY4NjgwLCJjdG0iOjE1ODU4NzY2ODAwNjQsImNpZCI6ImQ5ZDBuNEFadXAifQ.HMAADRs9WCAMa97WNO1ksUVtplddrbdNsPDQ70qvyIvFUwF0uGEC4L-R9_91_2HicKglDw6CPgAz8uHJVAHBNplSNkTVgWDwagN_mkbYnCi9lqripUYir1QRDroDRT57mH1aUgaLWVOMbHuFaMD3BmkS63MySozS8SEyW_4XcJ83Qa2FqxCPzbe7Ulc_P7y0CuQlOFKwyn2bGss0VICsXIcen_W9mFaRZdlmc-apvVSJthdftC822btwZzXTi3gEjKKcthemv26efCRc1tldpjgh_dFF2_vBYUUxJlnFUvOdPNaCtz-3JG14nFCS9uu1pAhzhjdx3zLEi4aXhitYNw; xqat=b4d6d8d0ad043e0f4370c514bad3097678175362; xq_r_token=f49395586f492df863a1f25fb6630d7c68e5185d; xq_is_login=1; u=6625580533; is_overseas=0; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1585876699"
var xuequeCookie = "_ga=GA1.2.528987204.1555945543; xq_a_token.sig=71HQ_PXQYeTyQvRDRGXoyAI8Cdg; xq_r_token.sig=QUTS2bLrXGdbA80soO-wu-fOBgY; snbim_minify=true; device_id=c8a242cd517399e92fd6562fe3c117c8; s=cx12eqso7r; bid=693c9580ce1eeffbf31bb1efd0320f72_k9ifcem7; Hm_lvt_1db88642e346389874251b5a1eded6e3=1588479908,1588497324,1588500208,1588725333; remember=1; xq_a_token=5e8099ac0db1c598a4f5a6e387ce8b475b55907d; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjY2MjU1ODA1MzMsImlzcyI6InVjIiwiZXhwIjoxNTkxMzE5NTQ5LCJjdG0iOjE1ODg3Mjc1NDk3NjAsImNpZCI6ImQ5ZDBuNEFadXAifQ.BxX9yHSOGmay23lKFDds6HCph2yoDFNbakT-KXDIcVf9-RdY-nSdTHwecvJIx5GeUKqL0yQACue8E7rdb_mWu2srL21IB-A38q2mXdQldd6hFlMnCf_YC1nmKy-D9VeWcG0i1kBdMxN_FJU5Ec9gq9Kz8skKd0KkIzmEpKVTo7TXpdH3KGUYEi30Peo8byzLGr1-jfI6cFDZOH2Ari5xcftDyKX1m6katCCVhax2WBvnVyVstgdR6ARDcXobYj8TUgA04ad87-MzHUN9hxWDFG2DnUW71JkSJylD6AKj08Uel7fG5Z8RohLpTTPf3xI0PVjtkzW4QDVIbpPuQlf8yQ; xqat=5e8099ac0db1c598a4f5a6e387ce8b475b55907d; xq_r_token=7d0878951d8ea7e00bba60070b2f3616df9c6198; xq_is_login=1; u=6625580533; is_overseas=0; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1588727553"
module.exports = {k_company,companys_task,dateString,query,connection,
    paralle_companys_task,xuequeCookie,xueqiuPostJson,xueqiuGetJson,companys_task_continue};