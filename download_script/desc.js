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
  
//var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=e7120e4e7b4be743f2c74067a44ee0e628770830; xq_a_token.sig=hE4WTsbi-zbUt506L09ZZbdJ_kI; xqat=e7120e4e7b4be743f2c74067a44ee0e628770830; xqat.sig=8PcFgZlZW0v0IH8MsTl27E3deIY; xq_r_token=be060178b1ebd6fa09c111bfbdd3b40db9e98dfc; xq_r_token.sig=WpxrkUwRX5LASIPyFu-1kPlaCJs; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; _gid=GA1.2.364037776.1551618045; aliyungf_tc=AQAAAIRMQWu3EQ4ACsd2e0ZdK3tv9E1U; Hm_lvt_1db88642e346389874251b5a1eded6e3=1551674476,1551680738,1551754280,1551766767; __utma=1.430870872.1550643434.1551422478.1551766799.20; __utmc=1; __utmb=1.1.10.1551766799; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1551767644";
var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; _gid=GA1.2.116983169.1552205760; xq_a_token=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xqat=fbc0017d2f2b4bc08c716edc5bd9d277c241eea6; xq_r_token=fcc1b1e4ddfb2bc4d55bfcccff1ba4b36e0091ff; xq_is_login=1; u=6625580533; xq_token_expire=Thu%20Apr%2004%202019%2020%3A06%3A35%20GMT%2B0800%20(CST); aliyungf_tc=AQAAAI7m835QIA0AvhvzcntW+6HhF2QE; Hm_lvt_1db88642e346389874251b5a1eded6e3=1552626756,1552633647,1552646787,1552661449; __utma=1.430870872.1550643434.1552500593.1552661457.41; __utmc=1; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1552667642";

function dateString(date){
    return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
}

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
function desc_all(){
    connection.query("select * from company where category_base!=9 and code='SH600613'",(err,companys)=>{
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
                    console.log('DONE!');
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
        Num(s)*0.01;
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
                    connection.query(`insert ignore into company_value values (${company.id},'${date}',${ttm},${pb},${value},${total},${earnings},${assets},${dividend},${_yield_},0,0)`,(error)=>{
                        if(error)console.error(error);
                    })
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
 * 下载全部公司的基本数据
 */
function base_all(){
    connection.query("select * from company where category_base!=9",(err,companys)=>{
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
                }else{
                    console.log('DONE!');
                }
            })
        }
    })
}

base_all();
//desc_all();
//desc_fetch({code:'SZ000725'},cb=>{console.log('done!')});
//base_fetch({code:'SZ002179'},cb=>{console.log('done!')});