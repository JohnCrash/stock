const {paralle_companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');
var Crawler = require("crawler");

/**
 * 现在单只股票的1分钟k线数据
 */
function k15_company(id,code,callback){
    let columns = [
        "timestamp",
        "volume",
        "open",
        "high",
        "low",
        "close",
        "chg",
        "percent",
        "turnoverrate"];
    function xueqiuURI(timestamp){
        //https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=SH000001&begin=1552960020000&period=1m&type=before&count=-224&indicator=kline
        let uri = `https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${code}&begin=${timestamp}&period=15m&type=before&count=-118&indicator=kline`;
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
    connection.query(`select max(timestamp) as r from k15_xueqiu where id=${id};`,(error, results, field)=>{
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
                                let dateString = `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}:0`;
                                let sqlStr;
                                if(head_date && date.getTime()===head_date.getTime()){
                                    //接头部分需要覆盖
                                    console.log(code,'update : ',dateString);
                                    let cols = columns.map((v,i)=>`${v}=${it[i]}`);
                                    sqlStr = `update k15_xueqiu set ${cols.slice(1).join()} where id=${id} and timestamp='${dateString}'`;
                                    needContinue = false;
                                }else{
                                    let cols = it.map((v)=>`${v}`);
                                    datas.push(`(${id},'${dateString}',${cols.slice(1).join()})`);
                                }

                                if(!needContinue)break;
                            }
                            /**
                             * 批量插入数据
                             */
                            if(datas.length>0){
                                console.log(code,'insert',datas.length);
                                connection.query(`insert ignore into k15_xueqiu values ${datas.join(',')}`,(error, results, field)=>{
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
            }
        });        
    });
}
/**
 * 更新每分钟k线数据k1_xueqiu
 */
function k15_companys(done){
    paralle_companys_task('id,code',10,com=>cb=>{
        k15_company(com.id,com.code,cb);
    }).then(usetime=>{
        if(done)done();
    }).catch(err=>{
        console.log(err);
        if(done)done();
    });
}

module.exports = {k15_companys,k15_company};