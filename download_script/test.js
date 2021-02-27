const {company_kline} = require('./xueqiu_kline')
//const {xueqiuCookie,initXueqiuCookie} = require('./k')
const Crawler = require("crawler");
const async = require("async");
const process = require('process');
const {base_fetch,backup_company_info,test_update_category,discard_category,update_company,test_companyByCategory,update_desc,desc_all,update_kechuanban} = require('./desc')
/*
process.argv.forEach(function(val, index, array) {
    console.log(index + ': ' + val);
  });

for( let i of process.argv){
    console.log(i);
}
*/

//xueqiuCookie((r)=>{
  
//})


/*
const redis = require("redis");
const client = redis.createClient();
 
client.on("error", function(error) {
  console.error(error);
});
 
client.get("XueqiuCookie",(err,reply)=>{
  console.log(err,reply)
});
*/
/*
initXueqiuCookie((b,c)=>{
  company_kline(8949,'SZ399006','d',(err,id)=>{
    console.log(err,id);
  });
})
*/
var xuequeCookie = ""
function getXueqiuCookie(){
    return xuequeCookie
}
//获取xueqiu网站的cookie
function initXueqiuCookie(cb){
    if(cb && xuequeCookie.length>0){
        cb(true,xuequeCookie)
        return
    }
    uri = "https://www.eastmoney.com/"
    let c = new Crawler({
        maxConnections : 1,
        callback : function(error, res, done){
            if(error)console.error(error);
            if(res.statusCode==200){
                cookie = "";
                for( it of res.headers['set-cookie']){
                    c = it.substr(0,it.search(';'))
                    if(c.substr(-1)!="="){
                        cookie += c
                        if(cookie!="")
                            cookie += "; "
                    }                        
                }
                xuequeCookie = cookie
                if(cb){
                    cb(true,cookie)
                }
            }else{
                console.error("xueqiuCookie",res.statusCode,res.boday);
                if(cb)
                    cb(false,null)
            }
            done();
        }
    });    
    c.queue({
        uri:uri
    });
}

initXueqiuCookie(null)