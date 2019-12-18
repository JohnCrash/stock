/**
 * 将K5,K15,KD数据都下载下来
 * 然后进行短线选股
 */
const {download_kline,company_kline} = require('./xueqiu_kline');
const {research_k15} = require('./research_k15');
const async = require('async');
const kline = [5,15,60,'d'];

download_kline(kline,(err)=>{
    if(err)
        console.error(err);
    else
    //    research_k15((e)=>{
    //        console.log('DONE!');
    //    });
});
