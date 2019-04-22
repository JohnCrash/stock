/**
 * 将K5,K15,KD数据都下载下来
 */
const {download_kline} = require('./xueqiu_kline');
const {download_kd} = require('./xueqiu_kd');
const async = require('async');
const kline = [5,15,60];

let task = [];

for(let lv of kline){
    task.push((cb)=>{
        console.log(`=========== DOWNLOAD ${lv} K line ============`);
        download_kline(lv,(err)=>{
            if(err)console.error(err);
            cb(err);
            console.log(`=========== ${lv} DONE ============`);
        });
    });
}
task.push((cb)=>{
    console.log(`=========== DOWNLOAD KD line ============`);
    download_kd((err)=>{
        if(err)console.error(err);
        cb(err);
        console.log(`=========== KD line DONE ============`);
    });
});

async.series(task,(err,result)=>{
    if(err)console.error(err);
    console.log('DONE!');
});
