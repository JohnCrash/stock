const {company_kline} = require('./xueqiu_kline')
const process = require('process');

process.argv.forEach(function(val, index, array) {
    console.log(index + ': ' + val);
  });

for( let i of process.argv){
    console.log(i);
}