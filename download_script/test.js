const {company_kline} = require('./xueqiu_kline')
const {xueqiuCookie} = require('./k')
const process = require('process');

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
const redis = require("redis");
const client = redis.createClient();
 
client.on("error", function(error) {
  console.error(error);
});
 
client.get("XueqiuCookie",(err,reply)=>{
  console.log(err,reply)
});
