//判断两个对象是不是相同
export function Eq(a,b){
    let ta = typeof(a);
    let tb = typeof(b);
    if(ta===tb){
        if(ta!=='object')
            return a===b;
        else{
            for(let k in a){
                if(!Eq(a[k],b[k]))return false;
            }
            return true;
        }
    }
    return false;
}

//取得一个时间的mysql日期
export function dateString(date){
    if(typeof(date)==='object')
        return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
    else if(typeof(date)==='string'){
        let d = new Date(date);
        return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`;
    }else
        return 'null';
}

export function timestampString(date){
    if(typeof(date)==='object')
        return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}`;
    else if(typeof(date)==='string'){
        let d = new Date(date);
        return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()} ${d.getHours()}:${d.getMinutes()}`;
    }else
        return 'null';
}

//取得两个日期的天数差
export function getDayLength(date0,date1){
    let d0,d1;
    if(typeof(date0)==='string'){
        d0 = new Date(date0);
        d1 = new Date(date1);
    }else{
        d0 = date0;
        d1 = date1;
    }
    return (d1-d0)/(3600*1000*24);
}

//枚举天
export function days(date0,date1){
    let r = [];
    let d0,d1;
    if(typeof(date0)==='object'){
        d0 = date0.getTime();
        d1 = date1.getTime();
    }else{
        d0 = new Date(date0).getTime();
        d1 = new Date(date1).getTime();
    }
    for(let d = d0;d<=d1;d+=(24*3600*1000)){
        r.push(new Date(d).toISOString());
    }       
    return r;
}