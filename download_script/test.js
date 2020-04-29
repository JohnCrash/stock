const {company_kline} = require('./xueqiu_kline')

bks = [
    [8941,'BK0040'],
    [8942,'BK0044']
]

lvs = [5,15,60,'d'];

const ucount_fast={
    "1":96*5*10,
    "5":96*10,
    "15":32*10,
    "30":16*10,
    "60":8*10,
    "120":4*10,
    'd':142
}

for( let c of bks){
    for(let lv of lvs){
        company_kline(c[0],c[1],lv,()=>{
            console.log('done!'+c[1])
        },ucount_fast)
    }
}
