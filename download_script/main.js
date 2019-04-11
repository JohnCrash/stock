const {paralle_companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');
const {macd,phase,calc_last_static30} = require('./macd');
const {k15_companys} = require('./xueqiu_k15');
const {k1_companys} = require('./xueqiu_k1');

//将company_value,company_detail,research_k15合并到单一的表company_select中去
query(`select * from company_detail`,`select * from company_value`,`select * from research_k15`).then(results=>{
    let detail = results[0];
    let value = results[1];
    let research = results[2];
    let ids = {};
    for(let i in detail){
        ids[detail[i].company_id] = {company_id:detail[i].company_id};
        ids[detail[i].company_id].detail_index = i;
    }
    for(let i in value){
        ids[value[i].company_id].value_index = i;
    }
    for(let i in research){
        ids[research[i].company_id].research_index = i;
    }
    let coms = [];
    for(let k in ids){
        let it = ids[k];
        let id = it.company_id;
        let d = detail[it.detail_index];
        let v = value[it.value_index];
        let r = research[it.research_index];
        if(d && v && r)
            coms.push(`(${id},'${d.name}','${d.code}','${d.category}',${v.ttm},${v.pb},${v.value},${v.total},${v.earnings},${v.assets},${v.dividend},${v.yield},${v.static30},${v.income30},${v.price},${r.k15_gain},${r.k15_drawal},${r.k30_gain},${r.k30_drawal},${r.k60_gain},${r.k60_drawal},${r.k120_gain},${r.k120_drawal},${r.kd_gain},${r.kd_drawal},${r.k15_max},${r.k15_maxdrawal},${r.k30_max},${r.k30_maxdrawal},${r.k60_max},${r.k60_maxdrawal},${r.k120_max},${r.k120_maxdrawal},${r.kd_max},${r.kd_maxdrawal})`);
    }
    query(`insert into company_select values ${coms.join(',')}`).then(result=>{
        console.log('DONE!');
    });
}).catch(err=>{
    console.error(err);
});
/*
k15_companys((err)=>{
    if(!err){
        k1_companys((err)=>{
            console.log('DONE!');
        });
    }
});
*/

//phase(1);
//calc_last_static30();
//macd((err)=>{
//    if(!err)console.log('DONE!');
//});   