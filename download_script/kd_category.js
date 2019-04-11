const {companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');

/**
 * 将分类的平均涨落存入到kd_category表中
 * n多少天的数据
 */
function kd_category(n){
    let cats = {};
    let dates = [];
    function KDRate(kd,rate){
        if(kd.length-1 === rate.length){
            for(let i=0;i<kd.length-1;i++){
                rate[i] += (kd[i].close-kd[i+1].close)/kd[i+1].close;
            }    
        }
        return rate;
    }
    companys_task('id,name,code,category',com=>cb=>{
        query(`select date,close from kd_xueqiu where id=${com.id} order by date desc limit ${n+1}`).then(
            kd=>{
                if(kd.length==n+1 && com.category>0){
                    let cat;
                    if(!cats[com.category]){
                        cat = {category:com.category,count:0,rate:new Array(n),acc:new Array(n)};
                        cats[com.category] = cat;
                        for(let i = 0;i<n;i++){
                            cat.rate[i] = 0;
                            cat.acc[i] = 0;
                        }
                    }else{
                        cat = cats[com.category];
                    }
                    cat.count++;
                    cat.rate = KDRate(kd,cat.rate);
                    console.log(com.name);
                }else{
                    if(com.id === 8828){
                        for(let i =0;i<kd.length-1;i++){
                            dates.push(dateString(kd[i].date));
                        }
                    }
                }
                cb();
            }
        )
    }).then(usetime=>{
        
        for(let k in cats){
            let c = cats[k];
            let  qs = [];
            for(let i=0;i<c.rate.length;i++){
                c.rate[i] /= c.count;
            }
            for(let i=c.rate.length-1;i>=0;i--){
                if(i==c.rate.length-1){
                    c.acc[i] = (1+c.rate[i]);
                }else{
                    c.acc[i] = c.acc[i+1]*(1+c.rate[i]);
                }
                qs.push(`(${c.category},'${dates[i]}',${c.rate[i]},${c.acc[i]})`);
            }
            query(`insert into kd_category values ${qs.join(',')}`).then().catch(err=>console.error(err));
        }
        
        console.log('DONE');
    }).catch(err=>{
        console.error(err);
    });
}

kd_category(60);

module.exports = {
    kd_category
};  
