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
    let timeKey = lv=='d'?'date':'timestamp';
    query(`select * from k${lv}_segment where id=${id} order by ${timeKey} desc limit 1`).then(result=>{
        let condition;
        if(result.length==1){
            let begin = result[0].timestamp;
            condition = `where id=${id} and ${timeKey} > '${begin}'`;
        }else{
            condition = '';
        }
        query(`select * from k${lv}_xueqiu ${condition} order by ${timeKey}`).then(R=>{

        }).catch(err=>{
            callback(err);
        });
    }).catch(err=>{
        if(err)console.error(err);
        callback(err);
    });
}

/**
 * 更新此级别的趋段
 */
function update_segment(lvs,done){
    companys_task('id,code,name',com=>cb=>{
        let task = [];
        for(let lv of lvs){
            task.push((callback)=>{
                update_company_segment(com.id,com.code,lv,callback);
            });
        }
        async.series(task,(err,result)=>{
            cb(err);
        });
    }).then(()=>{
        if(done)done();
    }).catch(err=>{
        console.error(err);
        if(done)done();
    });
}

module.exports = {update_segment};