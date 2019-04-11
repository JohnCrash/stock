const {paralle_companys_task,companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');
var Crawler = require("crawler");

/**
 * 现在单只股票的1分钟k线数据
 */
function k15_company(id,code,name,callback){
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
        "dea",
        "dif",
        "macd"];
    function xueqiuURI(timestamp){
        let uri = `https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${code}&begin=${timestamp}&period=15m&type=before&count=-3&indicator=kline,macd`;
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
    let c = new Crawler({
        maxConnections : 1,
        callback : function(error, res, done){
            if(error){
                console.error(code,error);
                callback(error);
            }else{
                try{
                    let sl = JSON.parse(res.body);
                    if(sl.data && sl.data.column && sl.data.item && sl.data.column.length===columns.length && sl.data.item.length && isCorrect(sl.data.column)){
                        let items = sl.data.item;

                        if(items.length===3){
                            /**
                             * index 5 close
                             * index 11 macd
                             */
                            let date = new Date(items[2][0]);
                            let timestamp = `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}:0`;                            
                            if(items[0][11]<0 &&items[1][11]<0&& items[2][11]>0){
                                console.log(code,name,items[2][5]);
                            //    query(`insert ignore into select15macd values (${id},'${timestamp}','${code}','${name}',${items[2][5]<30?1:0})`)
                                query(`update company_detail set k15macd=1 where company_id=${id}`)
                                .then()
                                .catch((err)=>{
                                    console.error(code,err);
                                });
                            }else if(items[0][11]<=0 && items[1][11]<=0 && items[2][11]<=0 && items[2][11]-items[1][11]>-items[2][11]){
                                query(`update company_detail set k15ready=1 where company_id=${id}`)
                                .then()
                                .catch((err)=>{
                                    console.error(code,err);
                                });
                            }
                        }
                        callback();
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
    c.queue({
        uri:xueqiuURI(Date.now()),
        headers:{
            Cookie:xuequeCookie,
        }
    });
}
/**
 * 更新每分钟k线数据k1_xueqiu
 */
function k15_select(done){
    query(`update company_detail set k15macd=0,k15ready=0`).then(()=>{
        paralle_companys_task('id,code,name',10,com=>cb=>{
            k15_company(com.id,com.code,com.name,cb);
        }).then(usetime=>{
            if(done)done();
        }).catch(err=>{
            console.log(err);
            if(done)done();
        });    
    }).catch(err=>{
        console.error(err);
        if(done)done();
    });
}

/**
 * 使用k15数据将个股和大盘进行比较
 */
function k15_compare(){
    function fluctuation(d){
        let f = [];
        for(let k of d){
            f.push((k.close-k.open)/k.open);
        }
        return f;
    }
    function compare(dap,sto,n){
        let glow = 0;
        let fall = 0;
        for(let i = 0;i<n;i++){
            let d = dap[i];
            let s = sto[i];
            if(d>0){
                glow += s/d;
            }else if(d<0){
                fall += s/d;
            }
        }
        return [glow,fall];
    }
    query(`select * from k15_xueqiu where id=8828 order by timestamp desc limit 32`).then(
        dapan32=>{
            let dapan = fluctuation(dapan32);

            companys_task('id,name,code',com=>cb=>{
                query(`select * from k15_xueqiu where id=${com.id} order by timestamp desc limit 32`).then(
                    stock32=>{
                        if(dapan32.length==stock32.length&&dapan32[0].timestamp.getTime()==stock32[0].timestamp.getTime()){ //时间范围一致
                            let stock = fluctuation(stock32);
                            //做比较
                            let [glow16,fall16] = compare(dapan,stock,16);
                            let [glow32,fall32] = compare(dapan,stock,32);
                            console.log(`${com.name}`);
                            query(`insert into k15_compare values (${com.id},'${com.name}',${glow16},${fall16},0,${glow32},${fall32},0)`);
                        }else{
                            console.log(`Ignore ${com.name}`);
                        }
                        cb();
                    }
                )
            }).then(usetime=>{
                console.log('DONE');
            }).catch(err=>{
            });    
        }
    ).catch(
        err=>{
            console.error(err);
        }
    );
}

/**
 * 取4个交易日数据比较涨跌进行分类
 */
function kd_binary4(){
    function binary(d,n){
        let b = 0;
        for(let i = 0;i<n;i++){
            b <<= 1;
            if(d[i].close-d[i].open>0){
                b |= 1;
            }
        }
        return b;
    }
    companys_task('id,name,code',com=>cb=>{
        query(`select * from kd_xueqiu where id=${com.id} order by date desc limit 6`).then(
            kd6=>{
                let bin4 = binary(kd6,4);
                let bin6 = binary(kd6,6);
                let glow = (kd6[0].close-kd6[0].open)/kd6[0].open;
                console.log(com.name);
                query(`update company_select set bin4=${bin4},bin6=${bin6},glow=${glow} where company_id=${com.id}`)
                cb();
            }
        )
    }).then(usetime=>{
        console.log('DONE');
    }).catch(err=>{
    });  
}
kd_binary4();
//k15_compare();

//k15_select(()=>{
//    console.log('DONE!!!');
//})