import {fetch} from 'whatwg-fetch';

function postJson(s,b,cb,errcb){
    fetch(s,{method:'POST',
    credentials: 'same-origin',
    headers: {'Content-Type': 'application/json'},
    body : JSON.stringify(b||{})})
    .then(response=>response.json())
    .then(json=>cb(json))
    .catch(err=>{
        errcb?errcb(err):console.error(err);
    });    
}

export {postJson}