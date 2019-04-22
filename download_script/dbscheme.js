
const CompanyScheme = {
    id:'number',
    code:'string',
    name:'string',
    category:'number',
    done:'number',
    kbegin:'string',
    kend:'string',
    amount:'number',
    amplitude:'number',
    chg:'number',
    current:'number',
    current_year_percent:'number',
    dividend_yield:'number',
    float_market_capital:'number',
    hast_follow:'number',
    lot_size:'number',
    pb:'number',
    pe_ttm:'number',
    percent:'number',
    percent5m:'number',
    tick_size:'number',
    type:'number',
    volume:'number',
    volume_ratio:'number'
};

const CategoryScheme = {
    id:'number',
    name:'string',
    code:'string',
    url:'string'
};

const DescriptScheme = {
    id:'number',
    name:'string',
    code:'string',
    desc:'string',
    site:'string',
    phone:'string',
    address:'string',
    business:'string'
};

const CompanySelectScheme = {
    company_id:'number',
    code:'string',
    name:'string',
    category:'string',
    ttm:'number',
    pb:'number',
    value:'number',
    total:'number',
    earnings:'number',
    assets:'number',
    dividend:'number',
    yield:'number',
    static30:'number', //30天静态增长
    static60:'number', //60天静态增长
    price:'number', //股价
    k15_gain:'number',
    k15_drawal:'number',
    k30_gain:'number',
    k30_drawal:'number',
    k60_gain:'number',
    k60_drawal:'number',
    k120_gain:'number',
    k120_drawal:'number',
    kd_gain:'number',
    kd_drawal:'number',
    k15_max:'number',
    k15_maxdrawal:'number',
    k30_max:'number',
    k30_maxdrawal:'number',
    k60_max:'number',
    k60_maxdrawal:'number',
    k120_max:'number',
    k120_maxdrawal:'number',
    kd_max:'number',
    kd_maxdrawal:'number',
    bin4:'number',
    glow:'number',
    ma5diff:'number',
    ma10diff:'number',
    ma20diff:'number',
    ma30diff:'number',
    bookmark15:'number',
    bookmark30:'number',
    bookmark60:'number',
    bookmark120:'number',
    bookmarkd:'number'
};

const K5Scheme={
    id:'number',
    date:'string',
    volume:"number",
    open:"number",
    high:"number",
    low:"number",
    close:"number",
    chg:"number",
    percent:"number",
    turnoverrate:"number",
    dea:'number',
    dif:"number",
    macd:'number'
};

const K15Scheme={
    id:'number',
    date:'string',
    volume:"number",
    open:"number",
    high:"number",
    low:"number",
    close:"number",
    chg:"number",
    percent:"number",
    turnoverrate:"number",
    dea:'number',
    dif:"number",
    macd:'number'
};

const K60Scheme={
    id:'number',
    date:'string',
    volume:"number",
    open:"number",
    high:"number",
    low:"number",
    close:"number",
    chg:"number",
    percent:"number",
    turnoverrate:"number",
    dea:'number',
    dif:"number",
    macd:'number'
};

const KDScheme={
    id:'number',
    date:'string',
    volume:"number",
    open:"number",
    high:"number",
    low:"number",
    close:"number",
    chg:"number",
    percent:"number",
    turnoverrate:"number",
    dea:'number',
    dif:"number",
    macd:'number'
};

function eqPair(t,scheme){
    let a = [];
    for(let k in t){
        if(scheme[k] === 'number'){
            a.push(`${k}=${t[k]}`);
        }else if(scheme[k] === 'string'){
            a.push(`${k}='${t[k]}'`);
        }
    }
    return a.join(',');
}

function valueList(t,scheme){
    let keys = [];
    let values = [];
    for(let k in t){
        if(scheme[k] === 'number'){
            keys.push(`${k}`);
            values.push(`${t[k]}`);
        }else if(scheme[k] === 'string'){
            keys.push(`${k}`);
            values.push(`'${t[k]}'`);
        }
    }
    return `(${keys.join(',')}) values (${values.join(',')})`;
}

function valueSeries(t,scheme){
    let a = [];
    for(let k in scheme){
        if(scheme[k]==='number'){
            if(typeof(t[k])==='number'){
                a.push(`${t[k]}`);
            }else{
                a.push(`null`);
            }
        }else if(scheme[k]==='string'){
            if(typeof(t[k])==='string'){
                a.push(`'${t[k]}'`);
            }else{
                a.push('null');
            }
        }
    }
    return a.join(',');
}

module.exports={
    CompanyScheme,
    CategoryScheme,
    DescriptScheme,
    CompanySelectScheme,
    K5Scheme,
    K15Scheme,
    K60Scheme,
    KDScheme,
    eqPair,
    valueList,
    valueSeries
};