const {companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');
const macd = require('macd');
const {update_company} = require('./desc');

function arrayScale(a,n){
    let s = [];
    for(let it of a){
        for(let i=0;i<n;i++)
            s.push(it);
    }
    return s;
}  
 
function tailArray(d,r){
    if(d && r){
        let a = [];
        for(let i=Math.floor(d.length*(1-r));i<d.length;i++){
            a.push(d[i]);
        }
        return a;
    }else return d;
}

function calcgain(k0,macd0,r){
    let lastK;
    let lastM;
    let buyK;
    let gain = 1;
    let maxdrawal = 0;
    let acc = 0;
    let k = tailArray(k0,r);
    let macd = tailArray(macd0,r);
    for(let i = 0;i<k.length;i++){
        let v = k[i];
        let m = macd[i];
        if(lastK){
            if(lastM<0 && m>0){
                buyK = v; 
            }else if(buyK && m<0){
                //trade(buyK,v);
                let r = v/buyK;
                gain = gain*r;

                if(r<1){
                    acc += (1-r);
                }else{
                    if(acc>maxdrawal)maxdrawal = acc;
                    acc = 0;
                }

                buyK = undefined;
            }  
        }
        lastK = v;
        lastM = m;
    }
    if(acc>maxdrawal)maxdrawal = acc;
    return [gain,maxdrawal>0?(gain-1)/maxdrawal:(gain-1)/0.1];
}

function calcgain_MAX(k0,macd0,r){
    let lastK;
    let lastM;
    let buyK;
    let maxK = 0;
    let gain = 1;
    let maxdrawal = 0;
    let acc = 0;
    let k = tailArray(k0,r);
    let macd = tailArray(macd0,r);    
    for(let i = 0;i<k.length;i++){
        let v = k[i];
        let m = macd[i];
        if(lastK){
            if(lastM<0 && m>0){
                buyK = v;
            }else if(buyK && m<0){
                //trade(buyK,v);
                let r = maxK/buyK;

                gain = gain*r;

                if(r<1){
                    acc += (1-r);
                }else{
                    if(acc>maxdrawal)maxdrawal = acc;
                    acc = 0;
                }

                buyK = undefined;
                maxK = 0;
            }
            if(buyK && v>maxK)maxK = v;
        }
        lastK = v;
        lastM = m;
    }
    if(acc>maxdrawal)maxdrawal = acc;
    return [gain,maxdrawal>0?(gain-1)/maxdrawal:(gain-1)/0.1];
}

function research_k15(done){
    query(`delete from research_k15`).then(result=>{
        companys_task('id',com=>cb=>{
            query(`select * from k15_xueqiu where id=${com.id}`).then(results=>{
                let k15close = [];
                let k30close = [];
                let k60close = [];
                let k120close = [];
                let kdclose = [];
                let length = results.length;
                console.log(com.id);
                results.forEach((k,i) => {
                    k15close.push(k.close);
                    if(i%2==0)k30close.push(k.close);
                    if(i%4==0)k60close.push(k.close);
                    if(i%8==0)k120close.push(k.close);
                    if(i%16==0)kdclose.push(k.close);            
                });
                let macd15 = macd(k15close).histogram;
                let macd30 = arrayScale(macd(k30close).histogram,2);
                let macd60 = arrayScale(macd(k60close).histogram,4);
                let macd120 = arrayScale(macd(k120close).histogram,8);
                let macdday = arrayScale(macd(kdclose).histogram,16);
                //减少数据量根据反应最近的变化
                let [k15gain,k15drawal] = calcgain(k15close,macd15,1/8);
                let [k30gain,k30drawal] = calcgain(k15close,macd30,1/4);
                let [k60gain,k60drawal] = calcgain(k15close,macd60,1/2);
                let [k120gain,k120drawal] = calcgain(k15close,macd120);
                let [kdgain,kddrawal] = calcgain(k15close,macdday);
                let startDate = dateString(results[0].timestamp);
                let endDate = dateString(results[results.length-1].timestamp);
                let [k15max,k15maxdrawal] = calcgain_MAX(k15close,macd15,1/8);
                let [k30max,k30maxdrawal] = calcgain_MAX(k15close,macd30,1/4);
                let [k60max,k60maxdrawal] = calcgain_MAX(k15close,macd60,1/2);
                let [k120max,k120maxdrawal] = calcgain_MAX(k15close,macd120);    
                let [kdmax,kdmaxdrawal] = calcgain_MAX(k15close,macdday);    
                query(`update company_select set k15_gain=${k15gain},k15_drawal=${k15drawal},k30_gain=${k30gain},k30_drawal=${k30drawal},k60_gain=${k60gain},k60_drawal=${k60drawal},k120_gain=${k120gain},k120_drawal=${k120drawal},kd_gain=${kdgain},kd_drawal=${kddrawal},
                k15_max=${k15max},k15_maxdrawal=${k15maxdrawal},k30_max=${k30max},k30_maxdrawal=${k30maxdrawal},k60_max=${k60max},k60_maxdrawal=${k60maxdrawal},k120_max=${k120max},k120_maxdrawal=${k120maxdrawal},kd_max=${kdmax},kd_maxdrawal=${kdmaxdrawal} where company_id=${com.id}`).then(results=>{
                    cb();
                }).catch(
                    err=>cb(err)
                );
            }).catch(err=>{
                cb(err);
            });
        }).then(usetime=>{
            console.log('DONE!');
            if(done)done();
        });
    }).catch(err=>{
        console.error(err);
        if(done)done(err);
    });    
}

research_k15();
module.exports = {research_k15};