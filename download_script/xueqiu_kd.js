/**
 * 专门用来下载雪球网的k线数据
 */
const {paralle_companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
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
    "ma5",
    "ma10",
    "ma20",
    "ma30",
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
    "ma5",
    "ma10",
    "ma20",
    "ma30",
    "dea",
    "dif",
    "macd"];
let column2index = {};
for(let k in columns){
    column2index[columns[k]] = k;
}
//incols是描述it的数据键,outcols是要输出的数据键,最后将组合成key=value,...
function str_pairs(it){
    let p = [];
    for(let k of dbcolumns){
        p.push(`${k}=${it[column2index[k]]}`);
    }
    return p.join(',');
}
//将dbcolumns中的值都输出value,...
function str_colums(it){
    let p = [];
    for(let k of dbcolumns){
        p.push(`${it[column2index[k]]}`);
    }
    return p.join(',');
}
const ucount={
    "1":96*5,
    "5":96,
    "15":32,
    "30":16,
    "60":8,
    "120":4
}
/**
 * 下载指定公司的kd数据
 */
function company_kd(id,code,callback){

    function xueqiuURI(timestamp){
        let uri = `https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${code}&begin=${timestamp}&period=day&type=before&count=-2&indicator=kline,ma,macd`;
        return uri;
    }
    function isCorrect(column){
        for(let i=0;i<column.length;i++){
            if(column[i]!=columns[i])return false;
        }
        return true;
    }
    /**
     * 第一步找到数据库中最近的一条记录
     */
    connection.query(`select max(date) as r from kd_xueqiu where id=${id};`,(error, results, field)=>{
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
                        if(sl.data && sl.data.column && sl.data.item && sl.data.column.length===columns.length && sl.data.item.length && isCorrect(sl.data.column) && nextdate!=sl.data.item[0][0]){
                            let needContinue = true;
                            let items = sl.data.item;
                            /**
                             * 这里批量插入数据
                             */
                            let datas = [];
                            for(let i=items.length-1;i>=0;i--){ //从最近的向过去处理
                                let it = items[i];
                                let date = new Date(it[0]);
                                let dateString = `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
                                let sqlStr;
                                if(date.getFullYear()<2013){ //不要更新2013年以前的数据了
                                    needContinue = false;
                                }
                                if(head_date && date.getTime()===head_date.getTime()){
                                    //接头部分需要覆盖
                                    console.log(code,'update : ',dateString);
                                    //let cols = columns.map((v,i)=>`${v}=${it[i]}`);
                                    //sqlStr = `update k1_xueqiu set ${cols.slice(1).join()} where id=${id} and timestamp='${dateString}'`;
                                    sqlStr = `update kd_xueqiu set ${str_pairs(it)} where id=${id} and date='${dateString}'`;
                                    connection.query(sqlStr,(error, results, field)=>{
                                        if(error){
                                            console.error(code,error);
                                        }
                                    });                                    
                                    needContinue = false;
                                }else{
                                    //let cols = it.map((v)=>`${v}`);
                                    //datas.push(`(${id},'${dateString}',${cols.slice(1).join()})`);
                                    datas.push(`(${id},'${dateString}',${str_colums(it)})`);
                                }

                                if(!needContinue)break;
                            }
                            /**
                             * 批量插入数据
                             */
                            if(datas.length>0){
                                console.log(code,'insert',datas.length);
                                connection.query(`insert ignore into kd_xueqiu values ${datas.join(',')}`,(error, results, field)=>{
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
                                        Cookie:xuequeCookie,
                                        Accept:'application/json, text/plain, */*'
                                    }
                                });
                            }else{
                                //console.log(code,'DONE');
                                callback();    
                            }
                        }else{
                            let err = res.body;
                            if(sl.data && sl.data.column && sl.data.item && sl.data.column.length===columns.length && sl.data.item.length && isCorrect(sl.data.column)){
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
            headers:{
                Cookie:xuequeCookie,
                Accept:'application/json, text/plain, */*'
            }
        });        
    });
}
/**
 * 下载kline数据
 * lv是k线级别1,5,15,30,60,120
 */
function download_kd(done){
    paralle_companys_task('id,code',10,com=>cb=>{
        company_kd(com.id,com.code,cb);
    }).then(usetime=>{
        if(done)done();
    }).catch(err=>{
        console.log(err);
        if(done)done();
    });
}

module.exports = {download_kd};