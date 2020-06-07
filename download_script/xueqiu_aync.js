/**
 * 同步雪球全部股票到company_select2
 */
const async = require("async");
const {companys_task,k_company,dateString,query,xueqiuPostJson,xueqiuGetJson} = require('./k');

//同步自选
 function xueqiu_company_aysnc(done){
    xueqiuGetJson('https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?size=1000&pid=-1&category=1',
    (err,json)=>{
        if(!err && json){
            if(json.data && json.data.stocks && json.data.stocks.length>0){
                //将数据更新到company_select2中
                query(`delete from company_select2 where source=0`)
                .then(results=>{
                    let tasks = []
                    for(let c of json.data.stocks){
                        tasks.push(cb=>{
                            query(`insert ignore into company_select2 values ('${c.symbol}','${c.name}',0)`).
                            then(result=>{
                                cb()
                            }).catch(err=>{
                                cb(err)
                            })
                        })
                    }
                    async.parallelLimit(tasks,5,(err)=>{
                        done(err)
                    })
                })
                .catch(err=>{
                    done(err)
                })
            }else done(err)
        }else done(err)
    })
 }

 module.exports = {xueqiu_company_aysnc};