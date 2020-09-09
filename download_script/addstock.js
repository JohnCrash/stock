const {company_kline} = require('./xueqiu_kline');
const {query,connection,initXueqiuCookie} = require('./k');
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
    initXueqiuCookie((b,c)=>{
    if(!b){
        console.error("初始化cookie失败");
        return;}
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
    })})
}

//每次只能加入一只股票
if(process.argv.length==4 || process.argv.length==5){
    if(process.argv.length==4)
        add_new_stock(process.argv[2],process.argv[3],null);
    else
        add_new_stock(process.argv[2],process.argv[3],process.argv[4]);
}else{
    ls = [
        ["SH510050","上证50ETF"],
        ["SH510300","沪深300ETF"],
        ["SH518880","黄金ETF"],
        ["SH515750","科技50ETF"],
        ["SH515650","消费50ETF"],
        ["SH512000","券商ETF"],
        ["SH515000","科技ETF"],
        ["SH512800","银行ETF"],
        ["SH512010","医药ETF"],
        ["SH512660","军工ETF"],
        ["SH512170","医疗ETF"],
        ["SH512980","传媒ETF"],
        ["SH512690","酒ETF"],
        ["SH510150","消费ETF"],
        ["SZ159996","家电ETF"],
        ["SZ159997","电子ETF"],
        ["SZ159994","5GETF"],
        ["SH512400","有色金属ETF"],
        ["SH515220","煤炭ETF"],
        ["SH515210","钢铁ETF"],
        ["SZ159930","能源ETF"],
        ["SH512580","环保ETF"]
    ]
    for( v of ls){
        add_new_stock(v[0],v[1],null)
    }
    //console.log('node addstock.js code category');
}