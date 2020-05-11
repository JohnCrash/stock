/**
 * 将K5,K15,KD数据都下载下来
 * 然后进行短线选股
 */
const {download_kline,company_kline} = require('./xueqiu_kline');
const {research_k15} = require('./research_k15');
const {xueqiu_company_aysnc} = require('./xueqiu_aync');
const async = require('async');
const process = require('process');
const kline = [5,15,60,'d'];

download_kline(kline,(err)=>{
    if(err)
        console.error(err);
    else
        xueqiu_company_aysnc(err=>{
            if(err){
                console.error(err);
                process.exit(-1);
            }else{
                console.log('DONE!');
                process.exit(0);
            }
        })    
    //    research_k15((e)=>{
    //        console.log('DONE!');
    //    });
});


