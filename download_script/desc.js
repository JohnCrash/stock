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
  
var xuequeCookie = "_ga=GA1.2.430870872.1550643434; device_id=5dc39f85a0a7e8f804d913c6f66bd411; s=f111o4ctz6; __utmz=1.1550648862.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=e7120e4e7b4be743f2c74067a44ee0e628770830; xq_a_token.sig=hE4WTsbi-zbUt506L09ZZbdJ_kI; xqat=e7120e4e7b4be743f2c74067a44ee0e628770830; xqat.sig=8PcFgZlZW0v0IH8MsTl27E3deIY; xq_r_token=be060178b1ebd6fa09c111bfbdd3b40db9e98dfc; xq_r_token.sig=WpxrkUwRX5LASIPyFu-1kPlaCJs; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6625580533; u.sig=ejkCOIwfh-8tPxr1D63z9yvqWK4; bid=693c9580ce1eeffbf31bb1efd0320f72_jsjwwtrv; _gid=GA1.2.364037776.1551618045; aliyungf_tc=AQAAAIRMQWu3EQ4ACsd2e0ZdK3tv9E1U; Hm_lvt_1db88642e346389874251b5a1eded6e3=1551674476,1551680738,1551754280,1551766767; __utma=1.430870872.1550643434.1551422478.1551766799.20; __utmc=1; __utmb=1.1.10.1551766799; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1551767644";

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

desc_all();
//desc_fetch({code:'SZ000725'},cb=>{console.log('done!')});