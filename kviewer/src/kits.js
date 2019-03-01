
function Eq(a,b){
    let ta = typeof(a);
    let tb = typeof(b);
    if(ta===tb){
        if(ta!=='object')
            return a===b;
        else{
            for(let k in a){
                if(a[k]!==b[k])return false;
            }
            return true;
        }
    }
    return false;
}

function dateString(date){
    if(date)
        return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
    else
        return 'null';
}
export {Eq,dateString};