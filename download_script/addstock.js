const {company_kline} = require('./xueqiu_kline');
const {query,connection} = require('./k');
const {CompanyScheme,valueList} = require("./dbscheme");
const process = require('process');

const ucount_fast={
    "1":96*5*10,
    "5":96*10,
    "15":32*10,
    "30":16*10,
    "60":8*10,
    "120":4*10,
    'd':142
};
/**
 * 作为一个标准的导入股票的入口
 */
function add_new_stock(code,name,category){
    //先检查是否存在
    query(`select id from company where code='${code}'`,`select id from company where name='${name}'`)
    .then(results=>{
        if(results[0].length==0&&results[1].length==0){
            //将code加入到company
            c = {
                code:code,
                name:name
            }
            if(category){
                c.category = category;
            }
            query(`insert ignore into company ${valueList(c,CompanyScheme)}`)
            .then(result=>{
                //开始下载数据
                lvs = [5,'d'];
                for(let lv of lvs){
                    company_kline(result.insertId,code,lv,()=>{
                        console.log(result.insertId,code,name,lv,'done!');
                    },ucount_fast)
                }
            })
            .catch(err=>{
                console.log(err)
            })
        }else{
            console.log('代码或者名字已经存在于company库中',code,name);
        }
    })
    .catch(err=>{
        console.log(err);
    })
}

//每次只能加入一只股票
if(process.argv.length==4 || process.argv.length==5){
    if(process.argv.length==4)
        add_new_stock(process.argv[2],process.argv[3],null);
    else
        add_new_stock(process.argv[2],process.argv[3],process.argv[4]);
}else{
    console.log('node addstock.js code category');
}