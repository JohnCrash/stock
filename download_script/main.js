const {macd,phase,calc_last_static30} = require('./macd');
const {k15_companys} = require('./xueqiu_k15');

k15_companys((err)=>{
    console.log('DONE',err);
});
//phase(1);
//calc_last_static30();
//macd((err)=>{
//    if(!err)console.log('DONE!');
//});