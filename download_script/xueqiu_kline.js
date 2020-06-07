/**
 * 专门用来下载雪球网的k线数据
 */
const {paralle_companys_task,companys_task_continue,k_company,dateString,query,connection,getXueqiuCookie,initXueqiuCookie} = require('./k');
const async = require('async');
const Crawler = require("crawler");

const columns = [
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
    "volume_post",
    "amount_post",    
    "dea",
    "dif",
    "macd"];
const dbcolumns = [
    "volume",
    "open",
    "high",
    "low",
    "close",
    "chg",
    "percent",
    "turnoverrate",
    "dea",
    "dif",
    "macd"];
let column2index = {};
for(let k in columns){
    column2index[columns[k]] = k;
}

const columns_d = [
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
    "volume_post",
    "amount_post",
    "ma5",
    "ma10",
    "ma20",
    "ma30",
    "dea",
    "dif",
    "macd"];
const dbcolumns_d = [
    "volume",
    "open",
    "high",
    "low",
    "close",
    "chg",
    "percent",
    "turnoverrate",
    "ma5",
    "ma10",
    "ma20",
    "ma30",
    "dea",
    "dif",
    "macd"];
let column2index_d = {};
for(let k in columns_d){
    column2index_d[columns_d[k]] = k;
}

//incols是描述it的数据键,outcols是要输出的数据键,最后将组合成key=value,...
function str_pairs(lv,it){
    let p = [];
    let dbcol = lv=='d'?dbcolumns_d:dbcolumns;
    let col2inx = lv=='d'?column2index_d:column2index;
    for(let k of dbcol){
        p.push(`${k}=${it[col2inx[k]]}`);
    }
    return p.join(',');
}
//将dbcolumns中的值都输出value,...
function str_colums(lv,it){
    let p = [];
    let dbcol = lv=='d'?dbcolumns_d:dbcolumns;
    let col2inx = lv=='d'?column2index_d:column2index;    
    for(let k of dbcol){
        p.push(`${it[col2inx[k]]}`);
    }
    return p.join(',');
}
const ucount={
    "1":96*5,
    "5":96,
    "15":32,
    "30":16,
    "60":8,
    "120":4,
    'd':2
}
//快速全部现在,将名称改为ucount
const ucount_fast={
    "1":96*5*10,
    "5":96*10,
    "15":32*10,
    "30":16*10,
    "60":8*10,
    "120":4*10,
    'd':142
}
/**
 * 下载指定公司的kline数据
 */
function company_kline(id,code,lv,callback,uctable=ucount){

    function xueqiuURI(timestamp){
        let uri;
        if(lv=='d')
            uri = `https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${code}&begin=${timestamp}&period=day&type=before&count=-${uctable[lv]}&indicator=kline,ma,macd`;
        else
            uri = `https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${code}&begin=${timestamp}&period=${lv}m&type=before&count=-${uctable[lv]}&indicator=kline,macd`;
        
        return uri;
    }
    function isCorrect(column){
        let cols = lv=='d'?columns_d:columns;
        if(column.length === cols.length){
            for(let i=0;i<column.length;i++){
                if(column[i]!=cols[i]){
                    console.error('1.xueqiu data modify',code,lv,column,cols);
                    return false;
                }
            }    
            return true;
        }else{
            console.error('2.xueqiu data modify',code,lv,column,cols);
            return false;
        }
    }
    /**
     * 第一步找到数据库中最近的一条记录
     */
    connection.query(`select max(${lv=='d'?'date':'timestamp'}) as r from k${lv}_xueqiu where id=${id};`,(error, results, field)=>{
        /**
         * 第二步覆盖最开头的数据
         */
        let head_date = error?null:results[0].r;
        let nextdate;
        let c = new Crawler({
            maxConnections : 1,
            callback : function(error, res, done){
                if(error){
                    console.error(code,error);
                    callback(error);
                }else{
                    try{
                        let sl = JSON.parse(res.body);
                        if(sl.data && sl.data.column && sl.data.item && sl.data.item.length && isCorrect(sl.data.column) && nextdate!=sl.data.item[0][0]){
                            let needContinue = true;
                            let items = sl.data.item;
                            /**
                             * 这里批量插入数据
                             */
                            let datas = [];
                            for(let i=items.length-1;i>=0;i--){ //从最近的向过去处理
                                let it = items[i];
                                let date = new Date(it[0]);
                                let sqlStr;
                                let dateString;
                                if(lv=='d'){
                                    if(date.getFullYear()<2000){ //不要更新2005年以前的数据了
                                        needContinue = false;
                                    }                                    
                                    dateString = `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
                                }else
                                    dateString = `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}:0`;
                                
                                if(head_date && date.getTime()===head_date.getTime()){
                                    //接头部分需要覆盖
                                    console.log(code,`update k${lv}: `,dateString);
                                    sqlStr = `update k${lv}_xueqiu set ${str_pairs(lv,it)} where id=${id} and ${lv=='d'?'date':'timestamp'}='${dateString}'`;
                                    connection.query(sqlStr,(error, results, field)=>{
                                        if(error){
                                            console.error(code,error);
                                        }
                                    });                                    
                                    needContinue = false;
                                }else{
                                    datas.push(`(${id},'${dateString}',${str_colums(lv,it)})`);
                                }

                                if(!needContinue)break;
                            }
                            /**
                             * 批量插入数据
                             */
                            if(datas.length>0){
                                console.log(code,`insert k${lv}: `,datas.length);
                                connection.query(`insert ignore into k${lv}_xueqiu values ${datas.join(',')}`,(error, results, field)=>{
                                    if(error){
                                        console.error(code,error);
                                    }
                                });
                            }
                            if(needContinue){
                                //console.log(code,'next segment : ',items[0][0]);
                                nextdate=items[0][0];
                                c.queue({
                                    uri:xueqiuURI(items[0][0]),
                                    headers:{
                                        Cookie:getXueqiuCookie(),
                                        Accept:'application/json, text/plain, */*'
                                    }
                                });
                            }else{
                                //console.log(code,'DONE');
                                callback();    
                            }
                        }else{
                            let err = res.body;
                            if(sl.data && sl.data.column && sl.data.item && sl.data.item.length && isCorrect(sl.data.column)){
                                //console.log(code,'DONE');
                                callback();
                            }else if(sl.data && sl.error_code==0){
                                //console.log(code,'NO K');
                                callback();                                
                            }else{
                                console.error(code,err);
                                callback(err);    
                            }
                        }
                    }catch(err){
                        console.error(code,err);
                        callback(err);
                    }
                }
                done();
            }
        });
        nextdate = Date.now();
        c.queue({
            uri:xueqiuURI(nextdate),
            jQuery: false,
            headers:{
                Cookie:getXueqiuCookie(),
                Accept:'application/json, text/plain, */*'
            }
        });        
    });
}
/**
 * 下载kline数据
 * lvs是k线级别1,5,15,30,60,120,'d'数组
 */
function download_kline(lvs,done){
    initXueqiuCookie((b,c)=>{
        if(b){
            companys_task_continue('id,code',1,com=>cb=>{
                let task = [];
                for(let lv of lvs){
                    task.push(
                        (callback)=>{
                            company_kline(com.id,com.code,lv,callback);
                        }
                    );    
                }
                async.series(task,(err,results)=>{
                    if(err)
                        console.error(err);
                    cb(err);
                });
            }).then(usetime=>{
                if(done)done();
            }).catch(err=>{
                console.log(err);
                if(done)done();
            });
        }
    })
}

module.exports = {download_kline,company_kline};