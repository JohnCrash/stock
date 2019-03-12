var mysql   = require('mysql');
var Crawler = require("crawler");
var async = require("async");
var bigint = require("big-integer");
var {companys_task,k_company,dateString,query,connection} = require('./k');
var {calc_tech_macd,calc_macd_wave,calc_macd_select} = require("./macd");

/*
var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; __utmz=1.1547831580.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.2077977505.1548294644; aliyungf_tc=AQAAAHwGH12l3ggA8M92e+oJhqNBY38L; xq_a_token=8dd2cc84915c45983930bb32e788dc93e0fcfddd; xq_a_token.sig=rjG2G1sq6nNdwvwGHxpwqDYbk3s; xq_r_token=5bb4c968b369150a382906ceba61eb8763282a13; xq_r_token.sig=eoelFajTh7zpqBNrEdBVD9rYjbw; u=661548299105754; Hm_lvt_1db88642e346389874251b5a1eded6e3=1548039323,1548194617,1548294644,1548299106; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1548299113; __utma=1.564054628.1547831580.1548294646.1548299113.13; __utmc=1; __utmt=1; __utmb=1.1.10.1548299113';
*/
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.2077977505.1548294644; xq_a_token=8dd2cc84915c45983930bb32e788dc93e0fcfddd; xq_a_token.sig=rjG2G1sq6nNdwvwGHxpwqDYbk3s; xq_r_token=5bb4c968b369150a382906ceba61eb8763282a13; xq_r_token.sig=eoelFajTh7zpqBNrEdBVD9rYjbw; Hm_lvt_1db88642e346389874251b5a1eded6e3=1548294644,1548299106,1548375753,1548463656; _gat_gtag_UA_16079156_4=1; u=721548463656672; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1548463660';
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.209931511.1550060636; xq_a_token=340cd8594a60098b3a9101bfed3c937ef2a41ae3; xq_a_token.sig=X5wPD5esioe_4cV4REojaNVJuMg; xq_r_token=9b4eeb50e2b16a45217033dcc55df006837cff00; xq_r_token.sig=Y3KOMJ2JkHB5ccV0Re2uvclcddY; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550060636,1550127249,1550203847,1550237793; u=441550237793218; _gat_gtag_UA_16079156_4=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550237806';
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.209931511.1550060636; xq_a_token=340cd8594a60098b3a9101bfed3c937ef2a41ae3; xq_a_token.sig=X5wPD5esioe_4cV4REojaNVJuMg; xq_r_token=9b4eeb50e2b16a45217033dcc55df006837cff00; xq_r_token.sig=Y3KOMJ2JkHB5ccV0Re2uvclcddY; u=741550318108222; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550203847,1550237793,1550285970,1550318108; _gat_gtag_UA_16079156_4=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550321763';
//var xuequeCookie = 's=ds1bgvygz9; device_id=e037be1499841fb99f5fe54a66e1240b; _ga=GA1.2.564054628.1547831580; Hm_lvt_fe218c11eab60b6ab1b6f84fb38bcc4a=1548040243; _gid=GA1.2.209931511.1550060636; xq_a_token=340cd8594a60098b3a9101bfed3c937ef2a41ae3; xq_a_token.sig=X5wPD5esioe_4cV4REojaNVJuMg; xq_r_token=9b4eeb50e2b16a45217033dcc55df006837cff00; xq_r_token.sig=Y3KOMJ2JkHB5ccV0Re2uvclcddY; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550237793,1550285970,1550318108,1550399051; u=561550399050848; _gat_gtag_UA_16079156_4=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550399365';
//var xuequeCookie = 'xq_a_token=0d73a36f00a0e985d381412742c39d12fb3ca56a; xq_a_token.sig=knknlVAPG2nkQ9enLy6gnEylv5w; xq_r_token=18d38484159ce73ae3451797d6517a41efa531b1; xq_r_token.sig=_SVEXsDz6FhNpFjXlGS8TPj_T7Q; _ga=GA1.2.1181448870.1550643624; _gid=GA1.2.230571212.1550643624; _gat=1; Hm_lvt_1db88642e346389874251b5a1eded6e3=1550643624; u=291550643626655; s=ds11jo7273; device_id=c23e116dd6bed04938f77815772ad027; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1550643643';
//var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=e7120e4e7b4be743f2c74067a44ee0e628770830; xq_a_token.sig=hE4WTsbi-zbUt506L09ZZbdJ_kI; xqat=e7120e4e7b4be743f2c74067a44ee0e628770830; xqat.sig=8PcFgZlZW0v0IH8MsTl27E3deIY; xq_r_token=be060178b1ebd6fa09c111bfbdd3b40db9e98dfc; xq_r_token.sig=WpxrkUwRX5LASIPyFu-1kPlaCJs; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; _gid=GA1.2.364037776.1551618045; aliyungf_tc=AQAAAIRMQWu3EQ4ACsd2e0ZdK3tv9E1U; Hm_lvt_1db88642e346389874251b5a1eded6e3=1551674476,1551680738,1551754280,1551766767; __utma=1.430870872.1550643434.1551422478.1551766799.20; __utmc=1; __utmb=1.1.10.1551766799; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1551767644";
var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; _gid=GA1.2.116983169.1552205760; xq_a_token=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xqat=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xq_r_token=fcc1b1e4ddfb2bc4d55bfcccff1ba4b36e0091ff; xq_is_login=1; u=6625580533; xq_token_expire=Thu%20Apr%2004%202019%2020%3A06%3A35%20GMT%2B0800%20(CST); aliyungf_tc=AQAAALeHCXbJlgEAnvGD3qvW+7mooFBG; Hm_lvt_1db88642e346389874251b5a1eded6e3=1552205761,1552219571,1552228090,1552267935; __utmc=1; snbim_minify=true; __utma=1.430870872.1550643434.1552267939.1552282682.34; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1552288329";

function dateString(date){
    return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
  }
/**
 * 从雪球玩获得行业分类表(主要下面代码没有排重)
 */
function category(){
    var c = new Crawler({
        maxConnections : 1,
        // This will be called for each crawled page
        callback : function (error, res, done) {
            if(error){
                console.log(error);
            }else{
                var $ = res.$;
                var li = $("[data-level2code]");
                connection.connect();
                for(let i=0;i<li.length;i++){
                    let it = li[i];
                    let href = it.attribs['href'];
                    let l2c = it.attribs['data-level2code'];
                    if(href && l2c && href.endsWith(l2c)){
                        //插入的数据库分类表中(没有排重)
                        connection.query(`insert ignore into category (name,code,url) values ('${it.attribs['title']}','${l2c}','${href}')`,(error, results, field)=>{
                            if (error){
                                console.log(error);
                                console.log(it.attribs['title']);
                                console.log(href);
                                console.log(l2c);
                            }else{
                                console.log('insert',it.attribs['title'])
                            }
                        });
                    }
                }
                connection.end();
            }
            done();
        }
    });
    
    c.queue('https://xueqiu.com/hq');
}

/**
 * 从雪球网获分类取公司名称和股票代码
 */
function companyByCategory(){
    function xueqiuURI(page,name,code){
        let uri = `https://xueqiu.com/industry/quote_order.json?page=${page}&size=30&order=desc&exchange=CN&plate=${name}&orderBy=percent&level2code=${code}&_=${Date.now()}`;
        console.log(uri);
        let encodeUri = encodeURI(uri);
        console.log(encodeUri);
        return encodeUri;
    }
    //遍历分类
    connection.query(`select * from stock.category`,(error, results, field)=>{
        if(error){
            console.log(error);
        }else{
            //这里使用异步库async来处理
            let tasks = [];
            for(let it of results){
                if(it.done!==0)continue; //已经做过了

                tasks.push((cb)=>{
                    let page = 1;
                    let timestamp = 0;
                    //处理指定的分类
                    let c = new Crawler({
                        maxConnections : 1,
                        callback : function (error, res, done) {
                            if(error || !res.body){
                                if(error)console.error(error);
                                console.error(it.name);
                                cb(null,it.name); //全部页面走完在调用完成
                            }else if(res.body){
                                let sl;
                                try{
                                    sl = JSON.parse(res.body);
                                    if(sl.data.length===0){
                                        cb(null,it.name); //全部页面走完在调用完成
                                        //标记分类已经完成
                                        connection.query(`update category set done = 1 where id=${it.id}`,(error, results, field)=>{
                                            if(error)console.error(error);
                                        });
                                    }else{
                                        //存储本业数据
                                        console.log(it.name,page-1);
                                        for(let company of sl.data){
                                            console.log(company.symbol,company.name);
                                            connection.query(`insert ignore into company (category,name,code) values ('${it.id}','${company.name}','${company.symbol}')`,(error, results, field)=>{
                                                if(error){
                                                    console.log(error);
                                                }
                                            });
                                        }
                                        //下一页
                                        c.queue({
                                            uri:xueqiuURI(page++,it.name,it.code),
                                            headers:{
                                                //在雪球网上刷新主页可以获得cookie
                                                Cookie:xuequeCookie,
                                            }
                                        });
                                    }                                    
                                }catch(e){
                                    console.error(it.name,page);
                                    cb(null,it.name); //全部页面走完在调用完成
                                }
                            }
                            done(); //一次请求结束
                        }
                    });
                    //这里进行分页
                    c.queue({
                        uri:xueqiuURI(page++,it.name,it.code),
                        headers:{
                            //在雪球网上刷新主页可以获得cookie
                            Cookie:xuequeCookie,
                        }
                    });
                });
            }
            async.series(tasks,(err,results)=>{
                if(err){
                    console.log(err);
                }else{
                    console.log('done');
                }
            });
        }
    });
}

/**
 * 沪深全部股票列表，没有分类的category=0
 */
function company(){
    function xueqiuURI(page){
        //https://xueqiu.com/stock/cata/stocklist.json?page=1&size=30&order=desc&orderby=percent&type=11%2C12&_=1547851466346
        let uri = `https://xueqiu.com/stock/cata/stocklist.json?page=${page}&size=30&order=desc&orderby=percent&type=11%2C12&_=${Date.now()}`;
        //console.log(uri);
        //let encodeUri = encodeURI(uri);
        //console.log(encodeUri);
        return uri;
    }
    let page = 1;
    let c = new Crawler({
        maxConnections : 1,
        callback : function(error, res, done){
            if(error){
                console.error(error);
            }else{
                try{
                    let sl = JSON.parse(res.body);
                    if(sl.stocks && sl.stocks.length>0){
                        for(let it of sl.stocks){
                            console.log(it.name,it.symbol);
                            connection.query(`insert ignore into company (category,name,code) values (0,'${it.name}','${it.symbol}')`,(error, results, field)=>{
                                if(error){
                                    console.log(error);
                                }
                            });                            
                        }
                        console.log('page',page);
                        c.queue({
                            uri:xueqiuURI(page++),
                            headers:{
                                Cookie:xuequeCookie,
                            }
                        });        
                    }else{
                        console.log(sl);
                        console.log('DONE');
                    }
                }catch(err){
                    console.error(err);
                }
            }
            done();
        }
    });
    c.queue({
        uri:xueqiuURI(page++),
        headers:{
            Cookie:xuequeCookie,
        }
    });
}

/**
 * 基础分类搜索
 */
function category_base(){
    function xueqiuURI(page,stockType){
        //创业  https://xueqiu.com/stock/quote_order.json?page=2&size=30&order=desc&exchange=CN&stockType=cyb&column=symbol%2Cname%2Ccurrent%2Cchg%2Cpercent%2Clast_close%2Copen%2Chigh%2Clow%2Cvolume%2Camount%2Cmarket_capital%2Cpe_ttm%2Chigh52w%2Clow52w%2Chasexist&orderBy=percent&_=1548041257127
        //沪市A https://xueqiu.com/stock/quote_order.json?page=1&size=30&order=desc&exchange=CN&stockType=sha&column=symbol%2Cname%2Ccurrent%2Cchg%2Cpercent%2Clast_close%2Copen%2Chigh%2Clow%2Cvolume%2Camount%2Cmarket_capital%2Cpe_ttm%2Chigh52w%2Clow52w%2Chasexist&orderBy=percent&_=1548041516354
        let uri = `https://xueqiu.com/stock/quote_order.json?page=${page}&size=30&order=desc&exchange=CN&stockType=${stockType}&column=symbol%2Cname%2Ccurrent%2Cchg%2Cpercent%2Clast_close%2Copen%2Chigh%2Clow%2Cvolume%2Camount%2Cmarket_capital%2Cpe_ttm%2Chigh52w%2Clow52w%2Chasexist&orderBy=percent&_=${Date.now()}`;
        //console.log(uri);
        //let encodeUri = encodeURI(uri);
        //console.log(encodeUri);
        return uri;
    }
    connection.query(`select * from category_base`,(error, results, field)=>{
        if(error){
            console.error(error);
        }else{
            for(let it of results){
                if(it.done)continue;
                let page = 1;
                let c = new Crawler({
                    maxConnections : 1,
                    callback : function(error, res, done){
                        if(error){
                            console.error(error);
                        }else{
                            try{
                                let sl = JSON.parse(res.body);
                                if(sl.data && sl.data.length>0){
                                    for(let ss of sl.data){
                                        console.log(ss[0],ss[1]);
                                        connection.query(`update company set category_base=${it.id} where code='${ss[0]}'`,(error, results, field)=>{
                                            if(error){
                                                console.error(error);
                                            }
                                        });                            
                                    }
                                    console.log('page',page);
                                    c.queue({
                                        uri:xueqiuURI(page++,it.code),
                                        headers:{
                                            Cookie:xuequeCookie,
                                        }
                                    });        
                                }else{
                                    //标记分类已经完成
                                    connection.query(`update category_base set done = 1 where id=${it.id}`,(error, results, field)=>{
                                        if(error)console.error(error);
                                    });
                                    console.log(sl);
                                    console.log('DONE',it.name);
                                }
                            }catch(err){
                                console.error(err);
                            }
                        }
                        done();
                    }
                });
                c.queue({
                    uri:xueqiuURI(page++,it.code),
                    headers:{
                        Cookie:xuequeCookie,
                    }
                });
            }
        }
    });

}
/**
 * 日K线
 * 允许多次调用，确保数据的连续于正确
 */
function kd_company(id,code,callback){
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
        "ma5",
        "ma10",
        "ma20",
        "ma30",
        "dea",
        "dif",
        "macd",
        "ub",
        "lb",
        "ma20",
        "kdjk",
        "kdjd",
        "kdjj",
        "rsi1",
        "rsi2",
        "rsi3",
        "wr6",
        "wr10",
        "bias1",
        "bias2",
        "bias3",
        "cci",
        "psy",
        "psyma"
    ];   
    /*
     * 一个排重插入的例子
     *  INSERT INTO users (full_name, login, password) 
     *  SELECT 'Mahbub Tito','tito',SHA1('12345') FROM DUAL
     *  WHERE NOT EXISTS 
     *  (SELECT login FROM users WHERE login='tito');
     */

    function xueqiuURI(date){
        //https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=SZ000063&begin=1529942400000&period=day&type=before&count=-142&indicator=kline,ma,macd,kdj,boll,rsi,wr,bias,cci,psy
        let uri = `https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=${code}&begin=${date}&period=day&type=before&count=-142&indicator=kline,ma,macd,kdj,boll,rsi,wr,bias,cci,psy`;
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
    connection.query(`SELECT MAX(date) as r FROM kd_xueqiu where id=${id};`,(error, results, field)=>{
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
                        if(sl.data && sl.data.column && sl.data.item && sl.data.column.length===33 && sl.data.item.length && isCorrect(sl.data.column) && nextdate!=sl.data.item[0][0]){
                            let needContinue = true;
                            let items = sl.data.item;
                            for(let i=items.length-1;i>=0;i--){ //从最近的向过去处理
                                let it = items[i];
                                let uuid = it[0]+id;//bigint(id).shiftLeft(32).or(it[0]);
                                let date = new Date(it[0]);
                                let dateString = `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
                                let sqlStr;
                                if(head_date && date.getTime()===head_date.getTime()){
                                    //接头部分需要覆盖
                                    console.log(code,'update : ',dateString);
                                    let cols = columns.map((v,i)=>`${v}=${it[i]}`);
                                    sqlStr = `update kd_xueqiu set ${cols.slice(1,18).join()},${cols.slice(19).join()} where id=${id} and date='${dateString}'`;
                                    needContinue = false;
                                }else{
                                    //如果存在指定的id和date就不插入，否则就插入
                                    console.log(code,'insert : ',dateString);
                                    //ma20重复了index在18
                                    let cols = it.map((v)=>`${v}`); //避免join出,,,
                                    sqlStr =`insert ignore into kd_xueqiu values (${id},'${dateString}',${cols.slice(1,18).join()},${cols.slice(19).join()})`;
                                }
                                connection.query(sqlStr,(error, results, field)=>{
                                    if(error){
                                        console.error(code,error);
                                    }
                                });
                                if(!needContinue)break;
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
                            if(sl.data && sl.data.column && sl.data.item && sl.data.column.length===33 && sl.data.item.length && isCorrect(sl.data.column)){
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
 * 计算公司id的日K的日期范围
 */
function kd_company_update_range(id,code,name,cb){
    connection.query(`SELECT min(date) as mins,max(date) as maxs FROM stock.kd_xueqiu where id=${id}`,(error, results, field)=>{
        if(error){
            console.error(code,name,error);
            cb(error);
        }else if(results.length===1&&results[0].mins&&results[0].maxs){
            let b = `${results[0].mins.getFullYear()}-${results[0].mins.getMonth()+1}-${results[0].mins.getDate()}`;
            let e = `${results[0].maxs.getFullYear()}-${results[0].maxs.getMonth()+1}-${results[0].maxs.getDate()}`;
            connection.query(`update company set kbegin='${b}',kend='${e}' where id=${id}`,(error, results, field)=>{
                if(error)
                    console.error(error);
                cb(error);
            });
        }else{
            console.log(code,name,'EMPTY!!!');
            cb();
        }
    });    
}
/**
 * 更新全部公司的kd数据
 * p = null,false,0完全更新
 * p = 1继续上次更新
 */
function kd_companys(p){
    //category_base=9的雪球上没有日K数据
    if(!p){
        connection.query('update company set done=0',(error, results, field)=>{
            if(error){
                console.error(error);
            }else{
                doit();
            }
        });
    }else{
        doit();
    }
    function doit(){
        connection.query('select * from company where category_base!=9 and done=0 order by id',(error, results, field)=>{
            if(error){
                console.error(error);
            }else{
                let a = [];
                for(let i=0;i<results.length;i++){
                    let it = results[i];
                    a.push(function(cb){
                        kd_company(it.id,it.code,(error)=>{
                            if(error){
                                connection.query(`delete from kd_xueqiu where id=${it.id}`,(error, results, field)=>{
                                    if(error)console.error(error);
                                });
                                cb(error);
                            }else{
                                connection.query(`update company set done=1 where id=${it.id}`,(error, results, field)=>{
                                    if(error){
                                        console.error(error);
                                        cb(error);
                                    }else{
                                        kd_company_update_range(it.id,it.code,it.name,(err)=>{
                                            console.log(it.code,it.name,'PASS');
                                            cb(err);
                                        });
                                    }
                                });    
                            }
                        });
                    });
                }
                //
                let total = results.length;
                let t = Date.now();
                console.log('Number of pending',total);
                async.parallelLimit(a,10,(err, results)=>{
                    //在做macd数据的时候要求k数据完整，如果在交易日中间获取数据就不能启动macd_all
                    //我简单的判断为排除星期1-5的早上9:30到下午3:00
                    if(!err){
                        let today = new Date();
                        let week = today.getDay();
                        let hours = today.getHours();
                        if( week>=1 && week<=5 && hours>9 && hours<15 ){
                            console.log(`Trading ${week} ${hours}!`);
                        }else{
                            calc_tech_macd((err)=>{
                                if(!err)calc_macd_wave((err)=>{
                                    if(!err)calc_macd_select((err)=>{
                                        if(!err)console.log('DONE!');
                                    });
                                });
                            });
                        }
                    }
                    connection.query('select count(*) as count from company where category_base!=9 and done=0 order by id',(error, results, field)=>{
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
 * 随机抽查公司的日K数据是否正确。f=1全部，f=0.1 抽查10%
 */
function kd_companys_check(f){
    //...
}

/**
 * macd快变正了或者刚刚变正的
 */
function macd_select(){
    let t0 = Date.now();
    console.log('handle select...');
    async.series([(cb)=>{
        connection.query('update company set cart=0',(err)=>cb(err));
    },(cb)=>{
        connection.query('update company_detail set cart=0',(err)=>cb(err));
    }],(err)=>{
        if(err)
            console.error(err);
        else{
            connection.query('select * from company where category_base!=9',(error,results,feild)=>{
                if(error)
                    console.error(error);
                else{
                    let tasks = [];
                    for(let com of results){
                        tasks.push((cb)=>{
                            macd_ready_positive(com,cb);
                        });
                    }
                    async.series(tasks,(err,results)=>{
                        if(err){
                            console.error(err);
                        }else{
                            connection.query('select count(id) as count from company where cart=1',(error,results,feild)=>{
                                if(error){
                                    console.error(error);
                                }else{
                                    console.log(`${results[0].count} to bo selected`);
                                    console.log(`use time ${(Date.now()-t0)/1000} second`);
                                }
                            });
                        }
                    })
                }
            })
        }
    });
}

kd_companys();
//macd_select();
