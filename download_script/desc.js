const {companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const Crawler = require("crawler");
const async = require("async");
const bigint = require("big-integer");
const {CompanyScheme,CompanySelectScheme,eqPair,valueList} = require("./dbscheme");

function desc_fetch(company,cb){
    let c = new Crawler({maxConnections : 1,
        callback:function(error,res,done){
            if(error){
                console.errror(error);
                cb(error);
            }else{
                try{
                    let $ = res.$;
                    let a = $(".profile-detail");
                    let link = $(".profile-link");
                    let contents = $(".widget-content");
                    if(a && a.length==1 && a[0].children && a[0].children.length){
                        let al = a[0].children.length;
                        let desc = a[0].children[0].data;
                        let address = al>6?a[0].children[6].data:"";
                        let phone = al>9?a[0].children[9].data:"";
                        let site = link&&link[0]&&link[0].children&&link[0].children[0]?link[0].children[0].attribs['href']:"";
                        let business = (contents&&contents[1]&&contents[1].children&&contents[1].children[0])?contents[1].children[0].data:"";
                        if(desc&&desc){
                            desc = desc.replace(/"/g,"");
                            desc = desc.replace(/'/g,"");
                            desc = desc.replace(/,/g,"，");
                            connection.query(`insert ignore into descript values (${company.id},'${company.name}','${company.code}','${desc}','${site}','${phone}','${address}','${business}')`,(error)=>{
                                if(error)console.error(error);
                            })
                        }else{
                            console.error(`Not found descript '${company.name}' ${company.code}.`);    
                        }
                    }else{
                        console.error(`Not found descript '${company.name}' ${company.code}`);
                    }
                    cb();
                }catch(err){
                    console.error(err,company.name,company.name);
                    cb(err);
                }
            }
            done();
        }});
    c.queue({
        uri:`https://xueqiu.com/S/${company.code}`,
        headers:{
            Cookie:xuequeCookie,
        } 
    });
}
/**
 * 下载全部公司描述数据
 */
function desc_all(done){
    connection.query("select * from company",(err,companys)=>{
        if(err){
            console.error(err);
        }else{
            let tasks = [];
            for(let company of companys){
                tasks.push(cb=>desc_fetch(company,cb));
            }
            async.parallelLimit(tasks,5,(err)=>{
                if(err){
                    console.error(err);
                }else{
                    console.log('desc_all DONE!');
                    if(done)done();
                }
            })
        }
    })
}

function strY(s){
    if(s[s.length-1]==='亿'){
        return Num(s.slice(0,-1))*100000000;
    }else{
        return Num(s)*100000000;
    }
}

function strS(s){
    if(s[s.length-1]==='%'){
        return Num(s.slice(0,-1))*0.01;
    }else{
        return Num(s)*0.01;
    }
}

function Num(s){
    try{
        let v = Number(s);
        if(isNaN(v))return 0;
        return v;
    }catch(e){
        return 0;
    }
}
function base_fetch(company,date,cb){
    let c = new Crawler({maxConnections : 1,
        callback:function(error,res,done){
            if(error){
                console.errror(error);
                cb(error);
            }else{
                try{
                    let $ = res.$;
                    let t2 = $(".separateBottom"); //数据都包括在这个表中
                    let t3 = t2.next();
                    let t4 = t3.next();
                    let t5 = t4.next();
                    //2-3 市盈率
                    let ttm = Num(t2[0].children[3].children[1].children[0].data);
                    //3-3 市净率
                    let pb = Num(t3[0].children[3].children[1].children[0].data);
                    //4-0 每股收益
                    let earnings = Num(t4[0].children[0].children[1].children[0].data);
                    //4-1 股息
                    let dividend = Num(t4[0].children[1].children[1].children[0].data);
                    //4-2 总股本
                    let total = strY(t4[0].children[2].children[1].children[0].data);
                    //4-3 总市值
                    let value = strY(t4[0].children[3].children[1].children[0].data);
                    //5-0 每股净资产
                    let assets = Num(t5[0].children[0].children[1].children[0].data);
                    //5-1 股息率
                    let _yield_ = strS(t5[0].children[1].children[1].children[0].data);
                    console.log(company.name,ttm,pb,value,total,earnings,assets,dividend,_yield_);
                    connection.query(`update company_select set ttm=${ttm},pb=${pb},value=${value},total=${total},earnings=${earnings},assets=${assets},dividend=${dividend},yield=${_yield_} where company_id=${company.id}`,(error)=>{
                        if(error)console.error(error);
                        cb();
                    });
                }catch(err){
                    console.error(err,company.name,company.name);
                    cb();
                }
            }
            done();
        }});
    c.queue({
        uri:`https://xueqiu.com/S/${company.code}`,
        headers:{
            Cookie:xuequeCookie,
        } 
    });
}
/**
 * 下载全部公司的基本数据(注意这个数据在companyByCategory中已经更新了因此可以不用调用这个函数)
 */
function update_desc(done){
    connection.query("select * from company",(err,companys)=>{
        if(err){
            console.error(err);
        }else{
            let tasks = [];
            let date = dateString(new Date());
            console.log(date);
            for(let company of companys){
                tasks.push(cb=>base_fetch(company,date,cb));
            }
            async.parallelLimit(tasks,5,(err)=>{
                if(err){
                    console.error(err);
                    if(done)done(err);
                }else{
                    console.log('DONE!');
                    if(done)done();
                }
            })
        }
    })
}

/**
 * 从雪球网获分类取公司名称和股票代码
 */
function companyByCategory(done){
    function xueqiuURI(page,name,code){
        let uri = `https://xueqiu.com/service/v5/stock/screener/quote/list?page=${page}&size=90&order=desc&order_by=percent&exchange=CN&market=CN&ind_code=${code}&_=${Date.now()}`;
        let encodeUri = encodeURI(uri);
        console.log(encodeUri);
        return encodeUri;
    }
    let companys = [];
    //遍历分类
    connection.query(`select * from stock.category`,(error, results, field)=>{
        if(error){
            console.log(error);
        }else{
            //这里使用异步库async来处理
            let tasks = [];
            for(let it of results){
                let a = it.url.split('=');
                it.code = a[a.length-1];
                tasks.push((cb)=>{
                    let page = 1;
                    let timestamp = 0;
                    //处理指定的分类
                    let c = new Crawler({
                        maxConnections : 1,
                        callback : function (error, res, done) {
                            if(error || !res.body){
                                if(error)console.error(error);
                                console.log(it.name);
                                cb(null,it.name); //全部页面走完在调用完成
                            }else if(res.body){
                                let sl;
                                try{
                                    sl = JSON.parse(res.body);
                                    if(sl.data.list.length===0){
                                        cb(null,it.name); //全部页面走完在调用完成
                                    }else{
                                        //存储本业数据
                                        console.log(it.name,page-1);
                                        for(let company of sl.data.list){
                                            console.log(it.id,company.symbol,company.name);
                                            //categoryID:it.id,companyName:company.name,companyCode:company.symbol}
                                            company.category = it.id;
                                            company.it = it;
                                            companys.push(company);
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
                                    console.error(e);
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
            async.parallelLimit(tasks,5,(err,results)=>{
                if(err){
                    console.log(err);
                    if(done)done(err);
                }else{
                    let tsk = [];
                    for(let com of companys){
                        tsk.push(cb=>{
                            //如果公司存在更新分类，如果不存在插入
                            query(`select id from company where code='${com.symbol}'`).then(result=>{
                                if(result.length>0){
                                    //存在
                                    console.log('update company',com.name);
                                    query(`update company set ${eqPair(com,CompanyScheme)} where code='${com.symbol}'`);
                                    //更新company_select
                                    //在company_select中字段category直接使用明文
                                    query(`select company_id from company_select where code='${com.symbol}'`).then(r=>{
                                        if(r.length>0){
                                            com.category = com.it.name;
                                            console.log('update company_select',com.name,com.category);
                                            if(com.symbol=='SH603068'){
                                                console.log(eqPair(com,CompanySelectScheme));
                                            }
                                            query(`update company_select set ${eqPair(com,CompanySelectScheme)} where code='${com.symbol}'`);    
                                        }else{
                                            com.code = com.symbol;
                                            com.company_id = result[0].id;
                                            com.category = com.it.name;
                                            console.log('insert company_select',com.company_id,com.name,com.category);
                                            query(`insert ignore into company_select ${valueList(com,CompanySelectScheme)}`);
                                        }
                                    });
                                }else{
                                    //不存在
                                    com.code = com.symbol;
                                    console.log('insert company',com.name);
                                    query(`insert ignore into company ${valueList(com,CompanyScheme)}`).then(r=>{
                                        query(`select id from company where code='${com.symbol}'`).then(r=>{
                                            query(`select company_id from company_select where code='${com.symbol}'`).then(R=>{
                                                if(R.length>0){
                                                    com.category = com.it.name;
                                                    console.log('update company_select',com.name,com.category);
                                                    if(com.symbol=='SH603068'){
                                                        console.log(eqPair(com,CompanySelectScheme));
                                                    }                                                    
                                                    query(`update company_select set ${eqPair(com,CompanySelectScheme)} where code='${com.symbol}'`);  
                                                }else{
                                                    com.code = com.symbol;
                                                    com.company_id = r[0].id;
                                                    com.category = com.it.name;
                                                    console.log('insert company_select',com.company_id,com.name,com.category);
                                                    query(`insert ignore into company_select ${valueList(com,CompanySelectScheme)}`);
                                                }
                                            });
                                        })
                                    })
                                }
                                cb();
                            }).catch(e=>{
                                console.error(e);
                                cb(e);
                            });
                        });
                    }
                    async.series(tsk,(error,results)=>{
                        if(error){
                            console.error(error);
                        }
                        console.log('done');
                        if(done)done(error);
                    })
                    
                }
            });
        }
    });
}

/**
 * 从雪球玩获得行业分类表(主要下面代码没有排重)
 */
function update_category(done){
    connection.query('delete from category',(error, results, field)=>{
        if(error){
            console.error(error);
        }else{
            var c = new Crawler({
                maxConnections : 1,
                // This will be called for each crawled page
                callback : function (error, res, callback) {
                    if(error){
                        console.log(error);
                    }else{
                        var $ = res.$;
                        var li = $("[data-level2code]");
                        for(let i=0;i<li.length;i++){
                            let it = li[i];
                            let href = it.attribs['href'];
                            let l2c = it.attribs['data-level2code'];
                            if(href && l2c && href.endsWith(l2c)){
                                //插入的数据库分类表中(没有排重)
                                console.log(it.attribs['title'],l2c);
                                connection.query(`insert ignore into category (name,code,url) values ('${it.attribs['title']}','${l2c}','${href}')`,(error, results, field)=>{
                                    if (error){
                                        console.error(error);
                                        console.log(it.attribs['title']);
                                        console.log(href);
                                        console.log(l2c);
                                    }else{
                                        console.log('insert',it.attribs['title'])
                                    }
                                });
                            }
                        }
                    }
                    callback();
                    if(done)done();
                }
            });
            
            c.queue('https://xueqiu.com/hq');
        }
    });
}

/**
 * 更新公司的数据包括company,category,company_select
 */
function update_company(done){
    update_category(err=>{
        if(err){
            if(done)done(err);
            return;
        }
        companyByCategory(err=>{
            if(err){
                if(done)done(err);
                return;
            }    
            update_desc(err=>{
                desc_all((err)=>{
                    if(done)done(err);
                });
            })
        });
    });
}

//update_company((err)=>{
//    console.log('DONE!');
//});
//update_desc((err)=>{
//    console.log('DONE!');
//});
module.exports = {update_company,update_desc};
