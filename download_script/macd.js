var mysql   = require('mysql');
var Crawler = require("crawler");
var async = require("async");
var bigint = require("big-integer");

var connection = mysql.createPool({
    connectionLimit : 10,
    host     : 'localhost',
    user     : 'root',
    password : 'nv30ati2',
    database : 'stock'
  });

  function dateString(date){
    return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
  }
  /**
   * 在macd从负数变成正数时买入，反之卖出
   * 创建数据库tech_macd
        CREATE TABLE `stock`.`tech_macd` (
        `id` INT NOT NULL AUTO_INCREMENT,
        `company_id` INT NULL,
        `buy_date` DATE NULL,
        `sell_date` DATE NULL,
        `buy_value` FLOAT NULL,
        `sell_value` FLOAT NULL,
        `rate_of_year` FLOAT NULL COMMENT '年收益率',
        PRIMARY KEY (`id`),
        UNIQUE INDEX `id_UNIQUE` (`id` ASC));
   */
function macd_company(id,code,kend,callback){
    let errmsg = 'repeat purchase';
    let t0 = Date.now();
    let total_income = 0; //总收益
    let positive_income = 0; //正收益
    let negative_income = 0; //负收益
    let total_num = 0; //总操作数
    let positive_num = 0;//正操作数
    let negative_num = 0;//负操作数
    let static_income = 0; //什么也不做长期投资收益率(第一次MACD操作和最后一次MACD操作间的差价)
    let hold_day = 0; //持股时间
    let begin_p,end_p;
    function sell(buy,cur){
        if(buy && cur){
            let buy_value = Math.abs(buy.open+buy.close)/2;
            let sell_value = Math.abs(cur.open+cur.close)/2;
            let dd = Math.floor((cur.date-buy.date)/(3600*24*1000));
            //每年股市开盘时间为243天
            let rate = ((sell_value-buy_value))/(buy_value);
            if(!begin_p)begin_p = buy;
            end_p = cur;
            total_income += rate;
            if(rate>0){
                positive_income+=rate;
                positive_num++;
            }else if(rate<0){
                negative_income+=rate;
                negative_num++;
            }
            hold_day += dd;
            total_num++;
            let sqlstr = `insert ignore into tech_macd values (${id},'${dateString(buy.date)}','${dateString(cur.date)}',${buy_value},${sell_value},${rate},${dd})`;
            //console.log(`insert ${code} ${rate}`);
            connection.query(sqlstr,(error, results, field)=>{
                if(error)console.error(code,error);
            });
        }
    }
    let endDate = dateString(new Date(kend));
    connection.query(`select date,open,close,macd from kd_xueqiu where id=${id} and date>'${endDate}'`,(error, results, field)=>{
        if(error){
            console.error(code,error);
            callback(error);
        }else{
            let flag;
            let buy;
            let t1 = Date.now();
            for(let i=0;i<results.length;i++){
                let it = results[i];
                if(it.macd>=0){
                    if(flag===-1){
                        if(!buy)
                            buy = it;
                    }
                    flag = 1;
                }else if(it.macd<0){
                    if(flag===1){
                        if(buy)
                            sell(buy,it);
                        buy = null;
                    }
                    flag = -1;
                }
            }
            if(end_p && begin_p && end_p.date && begin_p.date){
                let d = (end_p.date-begin_p.date)/(3600*24*1000);
                let usage_rate = hold_day/d;
                static_income = (end_p.close-begin_p.close)/begin_p.close;
                /* 这里不再更新sta_macd
                let sqlstr = `insert ignore into sta_macd values (${id},${total_income},${positive_income},${negative_income},${static_income},${total_num},${positive_num},${negative_num},${usage_rate},${hold_day})`;
                connection.query(sqlstr,(error, results, field)=>{
                    if(error)console.error(code,error);
                });
                */
                let c = Date.now();
                console.log(code,c-t1,t1-t0,total_num,total_income,results.length);
            }
            callback();
        }   
    });
}
/**
 * 处理全部公司的macd交易数据，将数据存储到teach_macd表中
 * 重复可重复调用进行差异化更新
 */
function macd_all(){
    let t0 = Date.now();
    console.log('handle macd_all...');
    connection.query('select * from company where category_base!=9',(error, results, field)=>{
        if(error){    
            console.error(error);
        }else{
            let a = [];
            let t1 = Date.now();
            for(let i=0;i<results.length;i++){
                let it = results[i];
                a.push(function(cb){
                    connection.query(`select max(sell_date) as b from tech_macd where company_id=${it.id}`,(error1, results1, field1)=>{
                        if(error1){
                            console.error(error1);
                            cb(error1);
                        }else if(results1.length>0){
                            console.log(it.code);
                            macd_company(it.id,it.code,(results1[0].b?results1[0].b:it.kbegin),(error)=>{
                                cb(error);
                            });        
                        }else{
                            let err = `select max(sell_date) as b from tech_macd where company_id .. return results1.length<=0 (${it.id})`;
                            console.error(err);
                            cb(err);
                        }
                    });    
                });
            }
            //
            let total = results.length;
            let t = Date.now();
            
            console.log('Number of pending',total,t-t1,t1-t0);
            async.series(a,(err, results)=>{
                connection.query('select count(*) as count from company where category_base!=9 and done=0',(error, results, field)=>{
                    if(error){
                        console.error(error);
                    }else{
                        console.log('Last time',total,'Current',results[0].count,'Processing completed',total-results[0].count);
                        console.log('Time cost',(Date.now()-t)/1000,'seconds');

                        macd_year();
                    }
                });
            });
        } 
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
                connection.query('select id,category from company where category_base!=9',(error, results, field)=>{
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

macd_all();
//macd_year();
//macd_wave();