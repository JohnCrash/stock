const {companys_task,k_company,dateString,query,connection,xuequeCookie} = require('./k');
const async = require('async');

/**
 * 对股票的涨落进行分类，将涨落基本一致的归为一类
 * n是比较多少个交易日的数据
 * r是相似率是多少就归为相似
 */
function classify(n){
    let kds = [];
    
    function Fluctuation(kd){
        let f = 0;
        for(let k of kd){
            f <<= 1;
            f |= (k.close-k.open>0?1:0);
        }
        return f;
    }
    function Diff(f0,f1){
        let a = f0^f1;
        let dif = 0;
        for(let i=0;i<n;i++){
            if(a & 1){
                dif++;
            }
            a>>=1;
        }
        return dif;
    }
    function UpdateClass(r,className){
        let R = Math.floor(n*(1-r));
        let clsID = 1;
        for(let i=0;i<kds.length;i++){
            let k0 = kds[i];
            if(!k0[className]){
                k0[className] = clsID;
                for(let j=i+1;j<kds.length;j++){
                    let k1 = kds[j];
                    if(!k1[className]){
                        let dif = Diff(k0.fluc,k1.fluc);
                        if(dif<=R){
                            k1[className] = clsID;
                        }
                    }
                }
                clsID++;
            }
            console.log(k0.name,className,k0[className]);
        }
    }
    companys_task('id,name,code',com=>cb=>{
        query(`select open,close from kd_xueqiu where id=${com.id} order by date desc limit ${n}`).then(
            kd=>{
                if(kd && kd.length===n){
                    console.log(com.name);
                    kds.push({id:com.id,name:com.name,code:com.code,fluc:Fluctuation(kd)});
                }else{
                    console.error(com.name,kd);
                }
                
                cb();
            }
        )
    }).then(usetime=>{
        UpdateClass(0.6,'class60');
        UpdateClass(0.7,'class70');
        UpdateClass(0.8,'class80');
        UpdateClass(0.9,'class90');
        for(let i=0;i<kds.length;i++){
            let k = kds[i];
            if(k.class60 && k.class70 && k.class80 && k.class90){
                query(`update company_select set class60=${k.class60},class70=${k.class70},class80=${k.class80},class90=${k.class90} where company_id=${k.id}`);
            }else{
                console.error(k.name);
            }
        }
        
        console.log('DONE');
    }).catch(err=>{
        console.error(err);
    });
}

classify(16);