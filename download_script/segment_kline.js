/**
 * 将kline图归纳为简单的趋势图
 */
const {companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');

/**
 * 更新此公司的趋段数据
 * 在此级别macd<0中找最低点，在macd>0中找最高点
 */
function update_company_segment(id,code,lv,callback){
    query(`select * from k${lv}_segment order by ${lv=='d'?'date':'timestamp'} desc limit 1`)
}

/**
 * 更新此级别的趋段
 */
function update_segment(lv,done){
    companys_task('id,code,name',com=>cb=>{
        update_company_segment(com.id,com.code,lv,cb);
    }).then(usetime=>{
        if(done)done();
    }).catch(err=>{
        console.log(err);
        if(done)done();
    });
}

module.exports = {update_segment};