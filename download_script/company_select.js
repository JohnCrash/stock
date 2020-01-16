const {paralle_companys_task,companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require("async");
const {CompanyScheme,CompanySelectScheme,eqPair,valueList} = require("./dbscheme");

function update_company(id,data){
    //数据已经时排过序的了最近的日期在最后面
    //==============================================================================
    //未完成，我决定使用python来完成这个工作，使用js调用python的方法追加到每次日更新结束后
    //见 status.py
    //==============================================================================
}
/**
 * 更新日期内的company_dvm数据
 */
function update_range(done,beginDate,endDate){
    sqlStr = `select id,date,volume,close,macd from kd_xueqiu where date>='${dateString(beginDate)}' and date<='${dateString(endDate)}'`
    connection.query(sqlStr,(error, results, field)=>{
        if(error){
            console.error(error);
            done(error);
        }else{
            idds = {};
            for( let i = 0;i<results.length;i++){
                d = results[i];
                if( !idds[d.id] )
                    idds[d.id] = [];

                idds[d.id].push(d);
            }
            for( let k in idds){
                update_company(k,idds[k]);
            }
            done();
        }
    });
}
/**
对所有股票进行计算
计算器日macd，周macd，日能量，周能量，日成交量kdJ,周成交量kdJ
算法是增量优化的，每次运行仅仅计算增加的部分
*/
function update_company_select(done){
    console.info('更新company_select...');
    //使用上证指数的日期为起始更新起始日期
    sqlStr = `select date from kd_xueqiu where id=8828 order by date desc limit 1`;
    connection.query(sqlStr,(error, results, field)=>{
        if(error){
            console.error(error);
            done(error);
        }else{
            if(results.length>0)
                endDate = results[0].date;
            else
                endDate = new Date();
            connection.query(`select date from company_dvm where id=8828 order by date desc limit 1`,(error2, results2, field2)=>{
                if(error2){
                    console.error(error2);
                    done(error2);
                }else{
                    if(results2.length>0)
                        beginDate = results2[0].date;
                    else
                        beginDate = new Date('2010-1-2'); //开始于2010年1月2日
                    console.info(`更新从'${dateString(beginDate)}'到'${dateString(endDate)}'的全部数据...`);
                    update_range(done,beginDate,endDate);
                }
            });
        }
    })
}
update_company_select((err)=>{

})
module.exports = {update_company_select};