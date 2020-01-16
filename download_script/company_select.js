const {paralle_companys_task,companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require("async");
const {CompanyScheme,CompanySelectScheme,eqPair,valueList} = require("./dbscheme");

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
            done(error)
        }else{
            if(results.length>0)
                beginDate = results[0].date;
            else
                beginDate = new Date();

            sqlStr = `select id,date,volume,open,high,low,close,macd from kd_xueqiu where date>='${dateString(beginDate)}'`
            done()
        }
    })
}
update_company_select((err)=>{

})
module.exports = {update_company_select};