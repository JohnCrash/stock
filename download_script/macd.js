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
function macd_company(id,code,callback){
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
            //console.log(sqlstr);
            connection.query(sqlstr,(error, results, field)=>{
                if(error)console.error(code,error);
            });
        }
    }
    connection.query(`select date,open,close,macd from kd_xueqiu where id=${id}`,(error, results, field)=>{
        if(error){
            console.error(code,error);
            callback(error);
        }else{
            let flag;
            let buy;
            let t1 = Date.now();
            for(let i=0;i<results.length;i++){
                let it = results[i];
                if(it.macd>0){
                    if(flag===-1){
                        if(!buy)
                            buy = it;
                        else
                            console.error(code,errmsg);
                    }
                    flag = 1;
                }else if(it.macd<0){
                    if(flag===1){
                        sell(buy,it);
                        buy = null;
                    }
                    flag = -1;
                }else{
                    if(flag===1){
                        sell(buy,it);
                        buy = null;
                    }else if(flag===-1){
                        if(!buy)
                            buy = it;
                        else
                            console.error(code,errmsg);
                    }
                }
            }
            if(end_p && begin_p && end_p.date && begin_p.date){
                let d = (end_p.date-begin_p.date)/(3600*24*1000);
                let usage_rate = hold_day/d;
                static_income = (end_p.close-begin_p.close)/begin_p.close;
                let sqlstr = `insert ignore into sta_macd values (${id},${total_income},${positive_income},${negative_income},${static_income},${total_num},${positive_num},${negative_num},${usage_rate},${hold_day})`;
                //console.log(sqlstr);
                connection.query(sqlstr,(error, results, field)=>{
                    if(error)console.error(code,error);
                });
                let c = Date.now();
                console.log(code,c-t1,t1-t0,total_num,total_income,results.length);
            }
            callback();
        }   
    });
}

//防止插入到tech_macd的数据出现重复
function macd_company2(id,code,callback){
    let t0 = Date.now();
    connection.query(`select company_id from sta_macd where company_id=${id}`,(error, results, field)=>{
        if(error){
            console.error(code,error);
            callback(error);
        }else{
            if(results.length===0){
                //先清理一下tech_macd
                let t1 = Date.now();
                connection.query(`delete from tech_macd where company_id=${id}`,(error, results, field)=>{
                    if(error){
                        console.error(code,error);
                        callback(error);
                    }else{
                        let c = Date.now();
                        console.log(code,'pending',c-t1,t1-t0);
                        macd_company(id,code,callback);
                    }
                });
            }else{
                callback();
            }
        }
    });
}
/**
 * 处理全部公司的macd策略
 * p = null,false,0(完全更新)
 * p = 1继续上次更新(如果失败)
 */
function macd_all(p){
    if(!p){
        connection.query('update company set done=0',(error, results, field)=>{
            if(error){
                console.error(error);
            }else{
                connection.query('delete from tech_macd',(error, results, field)=>{
                    if(error){
                        console.error(error);
                    }else{
                        doit();
                    }
                });
            }
        });
    }else{
        doit();
    }
    function doit(){
        let t0 = Date.now();
        connection.query('select * from company where category_base!=9 and done=0',(error, results, field)=>{
            if(error){
                console.error(error);
            }else{
                let a = [];
                let t1 = Date.now();
                for(let i=0;i<results.length;i++){
                    let it = results[i];
                    a.push(function(cb){
                        macd_company2(it.id,it.code,(error)=>{
                            if(error){
                                connection.query(`delete from tech_macd where company_id=${it.id}`,(error, results, field)=>{
                                    if(error)console.error(error);
                                });
                                cb(error);
                            }else{
                                connection.query(`update company set done=1 where id=${it.id}`,(error, results, field)=>{
                                    if(error){
                                        console.error(error);
                                    }
                                    cb(error);
                                });    
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
                        }
                    });
                });
            } 
        });
    }
}

/**
 * 将每一年的一只股票的数据统计到表sta_macd_year中去。
 * 基于tech_macd表中的数据
 */
function macd_year_company(id,cb){
    connection.query(`select * from tech_macd where company_id=${id}`,(error, results, field)=>{
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
            connection.query(`insert ignore into sta_macd_year values (${c.id},${i},${c.income},${c.positive_income},${c.negative_income},${c.static_income},${c.opertor_num},${c.positive_num},${c.negative_num},${c.usage_rate},${c.hold_day})`,(error)=>{
                if(error)console.error(error);
            });
        }
        cb(error);
    });
}
function macd_year(){
    connection.query('select id from company where category_base!=9',(error, results, field)=>{
        if(error){
            console.error(error);
        }else{
            let a = [];
            for(let i=0;i<results.length;i++){
                let it = results[i];
                a.push(function(cb){
                    console.log(it.id);
                    macd_year_company(it.id,(error)=>{
                        cb(error);
                    });
                });
            }  
            async.series(a,(err, results)=>{
                console.log(err,'DONE!');
            });
        }
    });
}
//macd_all();
//macd_company(134,'SH601318',(err)=>{console.log(err)});
macd_year();