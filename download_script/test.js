const {company_kline} = require('./xueqiu_kline')

bks = [
    [8932,'BK0055'],
    [8933,'BK0029'],
    [8934,'BK0033'],
    [8935,'BK0031'],
    [8936,'BK0066'],
    [8937,'BK0034'],
    [8938,'BK0638'],
    [8939,'BK0063'],
    [8940,'BK0022']
]

lvs = [5,15,60,'d'];

for( let c of bks){
    for(let lv of lvs){
        company_kline(c[0],c[1],lv,()=>{
            console.log('done!'+c[1])
        })
    }
}
