const {company_kline} = require('./xueqiu_kline')
const {xueqiuCookie,initXueqiuCookie} = require('./k')
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

initXueqiuCookie((b,c)=>{
  company_kline(8949,'SZ399006','d',(err,id)=>{
    console.log(err,id);
  });
})
