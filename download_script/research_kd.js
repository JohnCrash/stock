const {companys_task,k_company,dateString,query,connection,
    xuequeCookie,xueqiuPostJson,xueqiuGetJson} = require('./k');
const async = require('async');
const macd = require('macd');
const {CompanyScheme,CompanySelectScheme,eqPair,valueList} = require("./dbscheme");

function research_kd(done){
    companys_task('id',com=>cb=>{
        query(`select date,volume,high,low from kd_xueqiu where id = ${com.id} order by date desc limit 60`).then(R=>{
            if(R && R.length===60){
                let max60,max60price,min60,min60price,begin60price;
                let b;
                max60price = 0;
                min60price = 99999;
                begin60price = R[R.length-1].high;
                for(let i=R.length-1;i>=0;i--){
                    if(R[i].high>max60price){
                        max60price = R[i].high;
                        max60 = R[i].date;
                        b = i;
                    }
                }
                for(let i=b;i>=0;i--){
                    if(R[i].low<min60price){
                        min60price = R[i].low;
                        min60 = R[i].date;
                    }
                }
    
                let db = {max60,max60price,min60,min60price,begin60price};
                if(min60 && max60){
                    db.min60 = dateString(min60);
                    db.max60 = dateString(max60);
                    query(`update company_select set ${eqPair(db,CompanySelectScheme)} where company_id=${com.id}`).then(r=>{
                        cb();
                    }).catch(e=>{
                        console.error(e);
                        cb(e);
                    });
                }else{
                    cb();
                }
            }else{
                cb();
            }
        })
    }).then(usetime=>{
       console.log('research_kd DONE!');

       if(done)done();
    });   
}

function research_distributed(done){
    query(`SELECT distinct max60 FROM stock.company_select order by max60`).then(R=>{
        for(let it of R){
            if(it.max60){
                console.log(dateString(it.max60));
                query(`SELECT count(company_id) as count FROM stock.company_select where max60='${dateString(it.max60)}'`,`SELECT count(company_id) as count FROM stock.company_select where min60='${dateString(it.max60)}'`).then(results=>{
                    console.log(results);
                    if(results.length===2){
                        let maxn = results[0][0].count;
                        let minn = results[1][0].count;
                        query(`insert into distributed values ('${dateString(it.max60)}',${maxn},${minn})`);
                    }
                }).catch(e=>{
                    console.error(e);
                });
            }
        }
    }).catch(e=>{
        console.error(e);
    })
}

research_distributed();